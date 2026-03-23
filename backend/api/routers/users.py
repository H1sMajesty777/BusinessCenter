from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from api.database import get_db
from api.security import hash_password, decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

class UserCreate(BaseModel):
    login: str
    password: str
    email: Optional[str] = None
    role_id: int = 3

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

@router.post("/api/users", status_code=201, tags=["Users"])
def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)):
    """Создание пользователя — ТОЛЬКО АДМИН"""
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE login = %s OR email = %s", (user.login, user.email))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Логин или email уже занят")
    
    cursor.execute(
        "INSERT INTO users (login, password_hash, email, role_id, is_active) VALUES (%s, %s, %s, %s, TRUE) RETURNING id, login, email",
        (user.login, hash_password(user.password), user.email, user.role_id)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return {"id": row[0], "login": row[1], "email": row[2]}

@router.get("/api/users", tags=["Users"])
def get_users(current_user: dict = Depends(get_current_user)):
    """Список пользователей — ТОЛЬКО АДМИН"""
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, login, email, role_id, is_active FROM users ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "login": r[1], "email": r[2], "role_id": r[3], "is_active": r[4]} for r in rows]

@router.delete("/api/users/{user_id}", tags=["Users"])
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Удаление пользователя — ТОЛЬКО АДМИН"""
    require_admin(current_user)
    
    if str(current_user.get("sub")) == str(user_id):
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": f"Пользователь {user_id} удалён"}