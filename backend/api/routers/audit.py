from fastapi import APIRouter, HTTPException, Depends, Query, Request
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from api.database import get_db
from api.security import decode_token
from api.models.audit import AuditLogCreate, AuditLogResponse
from api.rate_limiter import limiter, RATE_LIMITS
# from api.security import get_current_user_from_cookie as get_current_user
from api.security import get_current_user 


router = APIRouter(prefix="/api/audit", tags=["Audit"])
# security = HTTPBearer(auto_error=False)


# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     Получить текущего пользователя из JWT токена
    
#     """
#     if not credentials:
#         raise HTTPException(status_code=401, detail="Нет токена")
    
#     token = credentials.credentials
#     payload = decode_token(token)
    
#     if not payload:
#         raise HTTPException(status_code=401, detail="Неверный токен")
    
#     return payload


def require_admin(current_user: dict):
    """
    Проверка роли: только админ
    
    """
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")


# ENDPOINTS

@router.get("", response_model=List[dict])
@limiter.limit(RATE_LIMITS["admin"])
def get_audit_log(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: dict = Depends(get_current_user)
):
    """
    Просмотр журнала действий
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.id, a.user_id, u.login, a.action_type, a.table_name, 
                   a.record_id, a.old_values, a.new_values, a.created_at 
            FROM audit_log a 
            LEFT JOIN users u ON a.user_id = u.id 
            ORDER BY a.created_at DESC 
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "user_id": r['user_id'],
                "user_login": r['login'],
                "action_type": r['action_type'],
                "table_name": r['table_name'],
                "record_id": r['record_id'],
                "old_values": r['old_values'],
                "new_values": r['new_values'],
                "created_at": str(r['created_at'])
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/stats", response_model=dict)
@limiter.limit(RATE_LIMITS["admin"])
def get_audit_stats(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Статистика журнала аудита
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Общее количество записей
        cursor.execute("SELECT COUNT(*) FROM audit_log")
        total = cursor.fetchone()['count']
        
        # Количество по типам действий
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM audit_log 
            GROUP BY action_type 
            ORDER BY count DESC
        """)
        by_type = cursor.fetchall()
        
        # Количество по таблицам
        cursor.execute("""
            SELECT table_name, COUNT(*) as count
            FROM audit_log 
            GROUP BY table_name 
            ORDER BY count DESC
        """)
        by_table = cursor.fetchall()
        
        # Количество записей за сегодня
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        today = cursor.fetchone()['count']
        
        return {
            "total_records": total,
            "today_records": today,
            "by_action_type": [
                {"action_type": r['action_type'], "count": r['count']} 
                for r in by_type
            ],
            "by_table": [
                {"table_name": r['table_name'], "count": r['count']} 
                for r in by_table
            ]
        }
    
    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201, response_model=dict)
@limiter.limit(RATE_LIMITS["admin"])
def create_audit_log(
    request: Request,
    log: AuditLogCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Создание записи в журнале аудита
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO audit_log (user_id, action_type, table_name, record_id, old_values, new_values, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                log.user_id,
                log.action_type,
                log.table_name,
                log.record_id,
                log.old_values,
                log.new_values,
                None  # created_at установится автоматически
            )
        )
        row = cursor.fetchone()
        conn.commit()
        
        return {"id": row['id'], "message": "Запись в журнал аудита создана"}
    
    finally:
        cursor.close()
        conn.close()