from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from api.database import get_db
from api.security import decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

class ApplicationCreate(BaseModel):
    office_id: int
    comment: Optional[str] = None

class ApplicationUpdate(BaseModel):
    status_id: int

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

def require_admin_or_manager(current_user: dict):
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")

@router.post("/api/applications", status_code=201, tags=["Applications"])
def create_application(app: ApplicationCreate, current_user: dict = Depends(get_current_user)):
    """
    Создание заявки на просмотр
    Доступ: Клиент (для себя) | Менеджер (для любого клиента)
    """
    user_id = current_user.get("sub")
    role_id = current_user.get("role_id")
    
    # Менеджер может создавать для клиентов, но нужен параметр client_id
    # Для простоты — все создают для себя
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO applications (user_id, office_id, status_id, comment, created_at) 
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (user_id, app.office_id, 1, app.comment, datetime.now())
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": row[0], "message": "Заявка создана"}

@router.get("/api/applications", tags=["Applications"])
def get_all_applications(current_user: dict = Depends(get_current_user)):
    """
    Просмотр всех заявок
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.user_id, u.login, a.office_id, o.office_number, a.status_id, s.name, a.comment, a.created_at 
        FROM applications a 
        JOIN users u ON a.user_id = u.id 
        JOIN offices o ON a.office_id = o.id 
        JOIN statuses s ON a.status_id = s.id 
        ORDER BY a.created_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"id": r[0], "user_id": r[1], "user_login": r[2], "office_id": r[3], "office_number": r[4], "status_id": r[5], "status_name": r[6], "comment": r[7], "created_at": str(r[8])} for r in rows]

@router.get("/api/applications/my", tags=["Applications"])
def get_my_applications(current_user: dict = Depends(get_current_user)):
    """
    Просмотр своих заявок
    Доступ: Клиент
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.office_id, o.office_number, a.status_id, s.name, a.comment, a.created_at 
        FROM applications a 
        JOIN offices o ON a.office_id = o.id 
        JOIN statuses s ON a.status_id = s.id 
        WHERE a.user_id = %s 
        ORDER BY a.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"id": r[0], "office_id": r[1], "office_number": r[2], "status_id": r[3], "status_name": r[4], "comment": r[5], "created_at": str(r[6])} for r in rows]

@router.put("/api/applications/{app_id}/status", tags=["Applications"])
def update_application_status(app_id: int, app_update: ApplicationUpdate, current_user: dict = Depends(get_current_user)):
    """
    Изменение статуса заявки
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE applications SET status_id = %s, reviewed_at = %s WHERE id = %s RETURNING id", (app_update.status_id, datetime.now(), app_id))
    
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": f"Статус заявки {app_id} обновлён"}