# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.database import get_db
from api.security import verify_password, create_token, decode_token
from api.models.user import LoginRequest, Token, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить текущего пользователя из токена"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload


@router.post("/login", response_model=Token)
def login(login_request: LoginRequest = Body(...)):
    """Вход в систему"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Поиск пользователя по логину
        cursor.execute(
            "SELECT id, login, password_hash, role_id, is_active FROM users WHERE login = %s",
            (login_request.login,)
        )
        user = cursor.fetchone()
        
        # Проверка существования
        if not user:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        user_id, user_login, password_hash, role_id, is_active = user
        
        # Проверка пароля
        if not verify_password(login_request.password, password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        # Проверка активности
        if not is_active:
            raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
        
        # Создание токена
        access_token = create_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id},
            expire_minutes=30
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Просмотр своего профиля"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, login, email, phone, full_name, role_id, is_active FROM users WHERE id = %s",
            (current_user.get("sub"),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return UserResponse(
            id=user[0],
            login=user[1],
            email=user[2],
            phone=user[3],
            full_name=user[4],
            role_id=user[5],
            is_active=user[6]
        )
    finally:
        cursor.close()
        conn.close()


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """Выход из системы"""
    return {"message": "Выход успешен"}