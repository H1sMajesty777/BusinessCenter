from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.database import get_db
from api.security import decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

def require_admin(current_user: dict):
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")

@router.get("/api/audit", tags=["Audit"])
def get_audit_log(current_user: dict = Depends(get_current_user)):
    """
    Просмотр журнала действий
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.user_id, u.login, a.action_type, a.table_name, a.record_id, a.created_at 
        FROM audit_log a 
        LEFT JOIN users u ON a.user_id = u.id 
        ORDER BY a.created_at DESC 
        LIMIT 100
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"id": r[0], "user_id": r[1], "user_login": r[2], "action_type": r[3], "table_name": r[4], "record_id": r[5], "created_at": str(r[6])} for r in rows]