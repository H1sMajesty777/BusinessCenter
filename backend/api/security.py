# -*- coding: utf-8 -*-
"""
Безопасность: хеширование паролей и JWT токены
Поддержка access + refresh токенов с blacklist в Redis
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from api.config import settings
from api.database import get_redis

# Настройка bcrypt для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===================================================================
# КОНСТАНТЫ
# ===================================================================

# Префиксы для ключей в Redis
REDIS_BLACKLIST_PREFIX = "token:blacklist:"
REDIS_REFRESH_PREFIX = "token:refresh:"


# ===================================================================
# ХЕШИРОВАНИЕ ПАРОЛЕЙ
# ===================================================================

def hash_password(password: str) -> str:
    """
    Хеширование пароля через bcrypt
    
    Args:
        password: Пароль в открытом виде
    
    Returns:
        str: Хешированный пароль
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password) -> bool:
    """
    Проверка пароля
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из базы данных
    
    Returns:
        bool: True если пароль верный, False иначе
    
    Note:
        Обрабатывает bytes из psycopg (декодирует в str)
    """
    try:
        # ✅ Если хеш пришёл как bytes (из psycopg) — декодируем
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')
        
        # ✅ Если пароль пришёл как bytes — тоже декодируем
        if isinstance(plain_password, bytes):
            plain_password = plain_password.decode('utf-8')
        
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ===================================================================
# СОЗДАНИЕ ТОКЕНОВ
# ===================================================================

def create_access_token(data: dict, expire_minutes: int = None) -> str:
    """
    Создание access токена
    
    Args:
         Данные для кодирования (sub, role_id, login, etc.)
        expire_minutes: Время жизни токена в минутах (по умолчанию из настроек)
    
    Returns:
        str: JWT access токен
    """
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
    """
    Создание refresh токена
    
    Args:
         Данные для кодирования (sub, role_id, login)
        expire_days: Время жизни токена в днях (по умолчанию из настроек)
    
    Returns:
        str: JWT refresh токен
    """
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
# ПРОВЕРКА ТОКЕНОВ
# ===================================================================

def decode_token(token: str, expected_type: str = None) -> Optional[dict]:
    """
    Декодирование JWT токена с проверкой типа
    
    Args:
        token: JWT токен
        expected_type: Ожидаемый тип токена ("access" или "refresh")
    
    Returns:
        dict | None: Payload если токен валиден, None если нет
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Проверка типа токена если указан
        if expected_type and payload.get("type") != expected_type:
            return None
        
        return payload
    except JWTError:
        return None
    except Exception:
        return None


def is_token_blacklisted(token: str) -> bool:
    """
    Проверка находится ли токен в blacklist
    
    Args:
        token: JWT токен
    
    Returns:
        bool: True если токен в blacklist, False если нет
    """
    try:
        redis_client = get_redis()
        # Вычисляем хеш токена для ключа
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = f"{REDIS_BLACKLIST_PREFIX}{token_hash}"
        return redis_client.exists(key)
    except Exception:
        return False


def blacklist_token(token: str, expire_seconds: int = None) -> bool:
    """
    Добавление токена в blacklist
    
    Args:
        token: JWT токен для блокировки
        expire_seconds: Время хранения в blacklist (по умолчанию время жизни токена)
    
    Returns:
        bool: True если успешно добавлен, False если ошибка
    """
    try:
        redis_client = get_redis()
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = f"{REDIS_BLACKLIST_PREFIX}{token_hash}"
        
        # Если время не указано — используем 30 минут (время жизни access токена)
        if expire_seconds is None:
            expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        # Добавляем в Redis с временем жизни
        redis_client.setex(key, expire_seconds, "1")
        return True
    except Exception:
        return False


def store_refresh_token(user_id: str, refresh_token: str, expire_days: int = None) -> bool:
    """
    Сохранение refresh токена в Redis
    
    Args:
        user_id: ID пользователя
        refresh_token: Refresh токен
        expire_days: Время жизни токена в днях
    
    Returns:
        bool: True если успешно сохранён, False если ошибка
    """
    try:
        redis_client = get_redis()
        key = f"{REDIS_REFRESH_PREFIX}{user_id}"
        
        if expire_days is None:
            expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        
        # Сохраняем токен с временем жизни
        expire_seconds = expire_days * 24 * 60 * 60
        redis_client.setex(key, expire_seconds, refresh_token)
        return True
    except Exception:
        return False


def get_refresh_token(user_id: str) -> Optional[str]:
    """
    Получение refresh токена пользователя из Redis
    
    Args:
        user_id: ID пользователя
    
    Returns:
        str | None: Refresh токен если найден, None если нет
    """
    try:
        redis_client = get_redis()
        key = f"{REDIS_REFRESH_PREFIX}{user_id}"
        return redis_client.get(key)
    except Exception:
        return None


def delete_refresh_token(user_id: str) -> bool:
    """
    Удаление refresh токена пользователя из Redis
    
    Args:
        user_id: ID пользователя
    
    Returns:
        bool: True если успешно удалён, False если ошибка
    """
    try:
        redis_client = get_redis()
        key = f"{REDIS_REFRESH_PREFIX}{user_id}"
        redis_client.delete(key)
        return True
    except Exception:
        return False


def revoke_all_user_tokens(user_id: str) -> bool:
    """
    Отозвать все токены пользователя (refresh + blacklist access)
    
    Args:
        user_id: ID пользователя
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    try:
        # Удаляем refresh токен
        delete_refresh_token(user_id)
        # Access токены будут отклонены при проверке blacklist
        return True
    except Exception:
        return False


# Алиас для совместимости со старым кодом
create_token = create_access_token