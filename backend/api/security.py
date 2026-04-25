# backend/api/security.py
# -*- coding: utf-8 -*-
"""
Безопасность: хеширование паролей и JWT токены
Поддержка access + refresh токенов с blacklist в Redis
HttpOnly Cookie для защиты от XSS
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Response, Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from api.config import settings
from api.database import get_redis


# Настройка bcrypt для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===================================================================
# КОНСТАНТЫ
# ===================================================================

REDIS_BLACKLIST_PREFIX = "token:blacklist:"
REDIS_REFRESH_PREFIX = "token:refresh:"


# ===================================================================
# ХЕШИРОВАНИЕ ПАРОЛЕЙ
# ===================================================================

def hash_password(password: str) -> str:
    """Хеширование пароля через bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password) -> bool:
    """Проверка пароля"""
    try:
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')
        if isinstance(plain_password, bytes):
            plain_password = plain_password.decode('utf-8')
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ===================================================================
# СОЗДАНИЕ ТОКЕНОВ
# ===================================================================

def create_access_token(data: dict, expire_minutes: int = None) -> str:
    """Создание access токена"""
    if expire_minutes is None:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expire_days: int = None) -> str:
    """Создание refresh токена"""
    if expire_days is None:
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expire_days)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ===================================================================
# COOKIE УПРАВЛЕНИЕ
# ===================================================================

def set_token_cookie(response: Response, access_token: str, refresh_token: str = None):
    """
    Установка HttpOnly Cookie с токенами
    
    Безопасность:
    - HttpOnly: недоступен для JavaScript (защита от XSS)
    - Secure: только по HTTPS (включается в production)
    - SameSite: Lax (защита от CSRF)
    """
    # Access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.cookie_secure,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    
    # Refresh token
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=settings.COOKIE_HTTPONLY,
            secure=settings.cookie_secure,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/auth/refresh"
        )


def clear_token_cookie(response: Response):
    """Очистка Cookie при выходе"""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")


def get_token_from_cookie(request: Request, token_type: str = "access") -> Optional[str]:
    """Извлечение токена из Cookie"""
    cookie_name = f"{token_type}_token"
    return request.cookies.get(cookie_name)


# ===================================================================
# ПРОВЕРКА ТОКЕНОВ
# ===================================================================

def decode_token(token: str, expected_type: str = None) -> Optional[dict]:
    """Декодирование JWT токена с проверкой типа"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


def is_token_blacklisted(token: str) -> bool:
    """Проверка находится ли токен в blacklist"""
    try:
        redis_client = get_redis()
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = f"{REDIS_BLACKLIST_PREFIX}{token_hash}"
        return redis_client.exists(key) > 0
    except Exception:
        return False


def blacklist_token(token: str, expire_seconds: int = None) -> bool:
    """Добавление токена в blacklist"""
    try:
        redis_client = get_redis()
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = f"{REDIS_BLACKLIST_PREFIX}{token_hash}"
        if expire_seconds is None:
            expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        redis_client.setex(key, expire_seconds, "1")
        return True
    except Exception:
        return False


def store_refresh_token(user_id: str, refresh_token: str, expire_days: int = None) -> bool:
    """Сохранение refresh токена в Redis"""
    try:
        redis_client = get_redis()
        key = f"{REDIS_REFRESH_PREFIX}{user_id}"
        if expire_days is None:
            expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        expire_seconds = expire_days * 24 * 60 * 60
        redis_client.setex(key, expire_seconds, refresh_token)
        return True
    except Exception:
        return False


def get_refresh_token(user_id: str) -> Optional[str]:
    """Получение refresh токена пользователя из Redis"""
    try:
        redis_client = get_redis()
        key = f"{REDIS_REFRESH_PREFIX}{user_id}"
        return redis_client.get(key)
    except Exception:
        return None


def delete_refresh_token(user_id: str) -> bool:
    """Удаление refresh токена пользователя из Redis"""
    try:
        redis_client = get_redis()
        key = f"{REDIS_REFRESH_PREFIX}{user_id}"
        redis_client.delete(key)
        return True
    except Exception:
        return False


def revoke_all_user_tokens(user_id: str) -> bool:
    """Отозвать все токены пользователя"""
    try:
        delete_refresh_token(user_id)
        return True
    except Exception:
        return False


create_token = create_access_token


# ===================================================================
# DEPENDENCY ДЛЯ ПОЛУЧЕНИЯ ПОЛЬЗОВАТЕЛЯ
# ===================================================================

async def get_current_user_from_cookie(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> dict:
    """
    Получение текущего пользователя из Cookie (с fallback на Authorization header)
    """
    token = None
    
    # 1. Пробуем взять из Cookie
    token = get_token_from_cookie(request, "access")
    
    # 2. Если нет - пробуем из заголовка (для мобильных приложений)
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Токен отозван")
    
    payload = decode_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload
get_current_user = get_current_user_from_cookie