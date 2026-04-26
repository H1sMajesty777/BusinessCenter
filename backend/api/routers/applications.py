from fastapi import APIRouter, HTTPException, Depends, Body, Request
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
from api.database import get_db
from api.security import decode_token
from api.models.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from api.rate_limiter import limiter, RATE_LIMITS
from api.security import get_current_user_from_cookie as get_current_user


router = APIRouter(prefix="/api/applications", tags=["Applications"])
# security = HTTPBearer(auto_error=False)


# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     Получить текущего пользователя из JWT токена
    
#     Args:
#         credentials: JWT токен из заголовка Authorization
    
#     Returns:
#         dict: Payload токена (sub, role_id, login, etc.)
    
#     Raises:
#         HTTPException: 401 если токена нет или он неверный
#     """
#     if not credentials:
#         raise HTTPException(status_code=401, detail="Нет токена")
    
#     token = credentials.credentials
#     payload = decode_token(token)
    
#     if not payload:
#         raise HTTPException(status_code=401, detail="Неверный токен")
    
#     return payload


def require_admin_or_manager(current_user: dict):
    """
    Проверка роли: только админ или менеджер
    
    Args:
        current_user: Данные текущего пользователя из токена
    
    Raises:
        HTTPException: 403 если роль не admin (1) или manager (2)
    """
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")


# ENDPOINTS

@router.post("", status_code=201, response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def create_application(request: Request, app: ApplicationCreate = Body(...), current_user: dict = Depends(get_current_user)):
    """
    Создание заявки на просмотр офиса
    Доступ: Все авторизованные (клиент для себя, менеджер для клиента)
    """
    user_id = current_user.get("sub")
    role_id = current_user.get("role_id")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка что офис существует
        cursor.execute("SELECT id FROM offices WHERE id = %s", (app.office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # Создание заявки (status_id=1 = новая заявка)
        cursor.execute(
            """INSERT INTO applications (user_id, office_id, status_id, comment, created_at) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (user_id, app.office_id, 1, app.comment, datetime.now())
        )
        row = cursor.fetchone()
        conn.commit()
        
        return {"id": row['id'], "message": "Заявка создана", "status": "новая"}
    
    finally:
        cursor.close()
        conn.close()


@router.get("", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_all_applications(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Просмотр всех заявок
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.id, a.user_id, u.login, a.office_id, o.office_number, 
                   a.status_id, s.name, a.comment, a.created_at 
            FROM applications a 
            JOIN users u ON a.user_id = u.id 
            JOIN offices o ON a.office_id = o.id 
            JOIN statuses s ON a.status_id = s.id 
            ORDER BY a.created_at DESC
        """)
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "user_id": r['user_id'],
                "user_login": r['login'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "status_id": r['status_id'],
                "status_name": r['name'],
                "comment": r['comment'],
                "created_at": str(r['created_at'])
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/my", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_my_applications(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Просмотр своих заявок
    Доступ: Все
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.id, a.office_id, o.office_number, a.status_id, s.name, 
                   a.comment, a.created_at 
            FROM applications a 
            JOIN offices o ON a.office_id = o.id 
            JOIN statuses s ON a.status_id = s.id 
            WHERE a.user_id = %s 
            ORDER BY a.created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "status_id": r['status_id'],
                "status_name": r['name'],
                "comment": r['comment'],
                "created_at": str(r['created_at'])
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.put("/{app_id}/status", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def update_application_status(request: Request, app_id: int, app_update: ApplicationUpdate = Body(...), current_user: dict = Depends(get_current_user)):
    """
    Изменение статуса заявки
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE applications SET status_id = %s, reviewed_at = %s WHERE id = %s RETURNING id",
            (app_update.status_id, datetime.now(), app_id)
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        conn.commit()
        
        return {"message": f"Статус заявки {app_id} обновлён", "new_status_id": app_update.status_id}
    
    finally:
        cursor.close()
        conn.close()


@router.delete("/{app_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def delete_application(request: Request, app_id: int, current_user: dict = Depends(get_current_user)):
    """
    Удаление заявки
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM applications WHERE id = %s RETURNING id", (app_id,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        conn.commit()
        
        return {"message": f"Заявка {app_id} удалена"}
    
    finally:
        cursor.close()
        conn.close()