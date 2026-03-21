# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from api.config import settings
import redis
import logging

logger = logging.getLogger(__name__)

# Настройка хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка Redis для черного списка токенов
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    redis_client.ping()
    logger.info("Redis connected successfully")
except Exception as e:
    redis_client = None
    logger.warning(f"Redis not available: {e}, using memory blacklist fallback")

# In-memory blacklist fallback
memory_blacklist = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def hash_password(password: str) -> str:
    """Хэширование пароля (алиас для get_password_hash)"""
    return get_password_hash(password)


def get_password_hash(password: str) -> str:
    """Хэширование пароля"""
    return pwd_context.hash(password)


def create_token(data: Dict[str, Any], expires_minutes: int) -> str:
    """Создание JWT токена"""
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Декодирование и проверка JWT токена"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Проверка, не в blacklist ли токен
        if is_token_blacklisted(token):
            logger.warning("Token is blacklisted")
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None


def blacklist_token(token: str, expire_minutes: int) -> None:
    """Добавление токена в черный список"""
    try:
        if redis_client:
            redis_client.setex(
                f"blacklist:{token}",
                expire_minutes * 60,
                "1"
            )
            logger.debug(f"Token blacklisted in Redis")
        else:
            memory_blacklist[token] = datetime.utcnow() + timedelta(minutes=expire_minutes)
            logger.debug(f"Token blacklisted in memory")
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")


def is_token_blacklisted(token: str) -> bool:
    """Проверка, находится ли токен в черном списке"""
    try:
        if redis_client:
            return redis_client.exists(f"blacklist:{token}") > 0
        else:
            # Очистка устаревших записей
            current_time = datetime.utcnow()
            expired_tokens = [
                t for t, exp in memory_blacklist.items()
                if exp < current_time
            ]
            for t in expired_tokens:
                del memory_blacklist[t]
            
            return token in memory_blacklist
    except Exception as e:
        logger.error(f"Error checking blacklist: {e}")
        return False


def save_refresh_token(user_id: int, token: str, expire_days: int) -> None:
    """Сохранение refresh токена в БД"""
    from api.database import get_db
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        expire_at = datetime.utcnow() + timedelta(days=expire_days)
        
        cursor.execute(
            """
            INSERT INTO refresh_tokens (user_id, token, expires_at, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (token) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                expires_at = EXCLUDED.expires_at,
                revoked = FALSE
            """,
            (user_id, token, expire_at)
        )
        conn.commit()
        logger.info(f"Refresh token saved for user {user_id}")
    except Exception as e:
        logger.error(f"Error saving refresh token: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def verify_refresh_token(user_id: int, token: str) -> bool:
    """Проверка refresh токена"""
    from api.database import get_db
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id FROM refresh_tokens 
            WHERE user_id = %s AND token = %s AND revoked = FALSE AND expires_at > NOW()
            """,
            (user_id, token)
        )
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def revoke_refresh_token(token: str) -> None:
    """Отзыв refresh токена"""
    from api.database import get_db
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE token = %s",
            (token,)
        )
        conn.commit()
        logger.info(f"Refresh token revoked")
    except Exception as e:
        logger.error(f"Error revoking refresh token: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_current_user(token: str = None) -> Optional[Dict[str, Any]]:
    """Получение текущего пользователя из токена"""
    if not token:
        return None
    return decode_token(token)