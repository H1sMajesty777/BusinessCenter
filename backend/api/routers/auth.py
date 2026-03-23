from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from api.database import get_db
from api.security import verify_password, create_token, decode_token
from api.models.user import LoginRequest, Token

router = APIRouter()
security = HTTPBearer(auto_error=False)

@router.post("/api/auth/login", response_model=Token, tags=["Auth"])
def login(request: LoginRequest = Body(...)):  # ← Явно указываем Body
    """Вход в систему и получение токена"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, login, password_hash, role_id, is_active FROM users WHERE login = %s",
        (request.login,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    if not verify_password(request.password, user[2]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    if not user[4]:
        raise HTTPException(status_code=400, detail="Аккаунт заблокирован")
    
    access = create_token({"sub": str(user[0]), "login": user[1], "role_id": user[3]}, 30)
    refresh = create_token({"sub": str(user[0]), "login": user[1]}, 10080)
    
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": 1800
    }

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получение текущего пользователя из токена"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload

@router.get("/api/auth/me", tags=["Auth"])
def get_me(current_user: dict = Depends(get_current_user)):
    """Данные текущего пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, login, email, role_id FROM users WHERE id = %s",
        (current_user.get("sub"),)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    role_names = {1: "admin", 2: "manager", 3: "client"}
    return {
        "id": user[0], 
        "login": user[1], 
        "email": user[2], 
        "role_id": user[3],
        "role": role_names.get(user[3], "unknown")
    }