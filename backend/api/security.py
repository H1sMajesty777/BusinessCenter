# backend/api/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from api.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, expire_minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None

def get_redis():
    """Ленивое подключение к Redis"""
    try:
        import redis
        return redis.Redis(host='localhost', port=6379, decode_responses=True)
    except:
        return None

def is_token_blacklisted(token: str) -> bool:
    try:
        redis = get_redis()
        if redis:
            return bool(redis.exists(f"blacklist:{token}"))
    except:
        pass
    return False

def blacklist_token(token: str, expire_minutes: int = 30):
    try:
        redis = get_redis()
        if redis:
            redis.setex(f"blacklist:{token}", expire_minutes * 60, "1")
    except:
        pass

def save_refresh_token(user_id: int, token: str, expire_days: int = 7):
    try:
        redis = get_redis()
        if redis:
            redis.setex(f"refresh:{user_id}:{token}", expire_days * 86400, "1")
    except:
        pass

def is_refresh_token_valid(user_id: int, token: str) -> bool:
    try:
        redis = get_redis()
        if redis:
            return bool(redis.exists(f"refresh:{user_id}:{token}"))
    except:
        pass
    return True

def delete_all_user_refresh_tokens(user_id: int):
    try:
        redis = get_redis()
        if redis:
            keys = redis.keys(f"refresh:{user_id}:*")
            if keys:
                redis.delete(*keys)
    except:
        pass