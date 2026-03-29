# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from api.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password) -> bool:
    """
    Проверка пароля
    
    ✅ ИСПРАВЛЕНО: обрабатываем bytes из базы данных
    """
    try:
        # ✅ Если хеш пришёл как bytes (из psycopg) — декодируем
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')
        
        # ✅ Если пароль пришёл как bytes (маловероятно) — тоже декодируем
        if isinstance(plain_password, bytes):
            plain_password = plain_password.decode('utf-8')
        
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_token(data: dict, expire_minutes: int) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Декодирование JWT токена"""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    except Exception:
        return None


# Алиас для совместимости
create_access_token = create_token