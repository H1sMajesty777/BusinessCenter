# backend/api/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Body, Request, Response
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime
from api.database import get_db, get_redis
from api.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, blacklist_token, store_refresh_token,
    delete_refresh_token, get_refresh_token, is_token_blacklisted,
    set_token_cookie, clear_token_cookie, get_token_from_cookie,
    settings
)
from api.models.user import LoginRequest, Token, UserResponse, TokenRefresh
from api.rate_limiter import limiter, RATE_LIMITS
# from api.security import get_current_user_from_cookie as get_current_user
from api.security import get_current_user 

router = APIRouter(prefix="/api/auth", tags=["Auth"])
# security = HTTPBearer(auto_error=False)


# async def get_current_user(
#     request: Request,
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#     """
#     Получить текущего пользователя из Cookie или Bearer токена
#     """
#     token = None
    
#     # Сначала пробуем взять из Cookie
#     token = get_token_from_cookie(request, "access")
    
#     # Если нет - пробуем из Bearer header
#     if not token and credentials:
#         token = credentials.credentials
    
#     if not token:
#         raise HTTPException(status_code=401, detail="Нет токена")
    
#     # Проверка blacklist
#     if is_token_blacklisted(token):
#         raise HTTPException(status_code=401, detail="Токен отозван")
    
#     payload = decode_token(token, expected_type="access")
#     if not payload:
#         raise HTTPException(status_code=401, detail="Неверный токен")
    
#     return payload


def require_admin(current_user: dict):
    """Проверка роли: только админ"""
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")


def require_admin_or_manager(current_user: dict):
    """Проверка роли: админ или менеджер"""
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")


# ===================================================================
# ENDPOINTS
# ===================================================================

@router.post("/login")
@limiter.limit(RATE_LIMITS["login"])
def login(
    request: Request,
    login_request: LoginRequest = Body(...),
    response: Response = None
):
    """
    Вход в систему с выдачей access + refresh токенов в HttpOnly Cookie
    Поддерживает вход как по логину, так и по email
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 🔥 ИЩЕМ ПО LOGIN ИЛИ EMAIL
        cursor.execute(
            """SELECT id, login, email, password_hash, role_id, is_active 
               FROM users WHERE login = %s OR email = %s""",
            (login_request.login, login_request.login)
        )
        user = cursor.fetchone()
        
        # Проверка существования
        if not user:
            raise HTTPException(status_code=401, detail="Неверный логин/email или пароль")
        
        user_id = user['id']
        user_login = user['login']  # возвращаем именно login, не email
        password_hash = user['password_hash']
        role_id = user['role_id']
        is_active = user['is_active']
        
        # Декодируем password_hash если он bytes
        if isinstance(password_hash, bytes):
            password_hash = password_hash.decode('utf-8')
        
        # Проверка пароля
        if not verify_password(login_request.password, password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин/email или пароль")
        
        # Проверка активности
        if not is_active:
            raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
        
        # Создаём токены
        access_token = create_access_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id}
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id}
        )
        
        # Устанавливаем Cookie
        set_token_cookie(response, access_token, refresh_token)
        
        # Сохраняем refresh токен в Redis
        store_refresh_token(str(user_id), refresh_token)
        
        # Возвращаем информацию о пользователе
        return {
            "message": "Успешный вход",
            "user": {
                "id": user_id,
                "login": user_login,
                "email": user['email'],
                "role_id": role_id
            }
        }
    
    finally:
        cursor.close()
        conn.close()


@router.post("/refresh")
@limiter.limit(RATE_LIMITS["authenticated"])
def refresh_token(
    request: Request,
    response: Response
):
    """
    Обновление access токена через refresh токен из Cookie
    """
    # Берём refresh токен из Cookie
    refresh_token = get_token_from_cookie(request, "refresh")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Нет refresh токена")
    
    payload = decode_token(refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный refresh токен")
    
    user_id = payload.get("sub")
    user_login = payload.get("login")
    role_id = payload.get("role_id")
    
    # Проверяем что refresh токен хранится в Redis
    stored_token = get_refresh_token(user_id)
    if not stored_token or stored_token != refresh_token:
        raise HTTPException(status_code=401, detail="Refresh токен отозван или не найден")
    
    # Проверяем что пользователь всё ещё активен
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT is_active FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user or not user['is_active']:
            # Удаляем refresh токен если пользователь заблокирован
            delete_refresh_token(user_id)
            raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
        
        # Создаём новый access токен
        new_access_token = create_access_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id}
        )
        
        # Обновляем Cookie
        set_token_cookie(response, new_access_token)
        
        return {"message": "Токен обновлён"}
    
    finally:
        cursor.close()
        conn.close()


# backend/api/routers/auth.py

@router.get("/me", response_model=UserResponse)
@limiter.limit(RATE_LIMITS["authenticated"])
async def get_me(request: Request, current_user: dict = Depends(get_current_user)):
    """Проверка текущего пользователя — работает с HttpOnly Cookie"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT id, login, email, phone, full_name, role_id, is_active, created_at 
               FROM users WHERE id = %s""",
            (current_user.get("sub"),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return UserResponse(
            id=user['id'],
            login=user['login'],
            email=user['email'],
            phone=user['phone'],
            full_name=user['full_name'],
            role_id=user['role_id'],
            is_active=user['is_active'],
            created_at=user['created_at']
        )
    finally:
        cursor.close()
        conn.close()


@router.post("/logout")
@limiter.limit(RATE_LIMITS["authenticated"])
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    Выход из системы с отзывом всех токенов
    
    Access токен добавляется в blacklist
    Refresh токен удаляется из Redis
    Cookie очищаются
    """
    user_id = current_user.get("sub")
    
    # Получаем токен для добавления в blacklist
    token = get_token_from_cookie(request, "access")
    if token:
        blacklist_token(token)
    
    # Удаляем refresh токен из Redis
    delete_refresh_token(user_id)
    
    # Очищаем Cookie
    clear_token_cookie(response)
    
    return {
        "message": "Выход успешен",
        "detail": "Все токены отозваны. Cookie очищены."
    }


@router.post("/logout/all")
@limiter.limit(RATE_LIMITS["authenticated"])
async def logout_all(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    Выход со всех устройств (отзыв всех токенов пользователя)
    """
    user_id = current_user.get("sub")
    
    # Удаляем refresh токен
    delete_refresh_token(user_id)
    
    # Очищаем Cookie
    clear_token_cookie(response)
    
    return {
        "message": "Выход со всех устройств успешен",
        "detail": "Все токены отозваны. Необходимо войти заново."
    }


# Для обратной совместимости - получение токена в теле (только для мобильных приложений)
@router.post("/mobile/login", response_model=Token)
@limiter.limit(RATE_LIMITS["login"])
def mobile_login(request: Request, login_request: LoginRequest = Body(...)):
    """
    Вход для мобильных приложений - токены в JSON теле (не в Cookie)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT id, login, password_hash, role_id, is_active 
               FROM users WHERE login = %s""",
            (login_request.login,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        user_id = user['id']
        user_login = user['login']
        password_hash = user['password_hash']
        role_id = user['role_id']
        is_active = user['is_active']
        
        if isinstance(password_hash, bytes):
            password_hash = password_hash.decode('utf-8')
        
        if not verify_password(login_request.password, password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        if not is_active:
            raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
        
        access_token = create_access_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id}
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id}
        )
        
        store_refresh_token(str(user_id), refresh_token)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
    
    finally:
        cursor.close()
        conn.close()