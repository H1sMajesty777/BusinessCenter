# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional
import logging
import traceback

from api.database import get_db
from api.security import (
    verify_password,
    create_token,
    decode_token,
    blacklist_token,
    save_refresh_token
)
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    login: str
    email: Optional[str] = None
    role_id: int


@router.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(login_data: LoginRequest):
    """Аутентификация пользователя"""
    conn = None
    cursor = None
    
    try:
        logger.info(f"Login attempt for user: {login_data.login}")
        
        # Получаем соединение с БД
        conn = get_db()
        cursor = conn.cursor()
        
        # Запрос пользователя
        cursor.execute(
            """
            SELECT id, login, password_hash, role_id, is_active, email
            FROM users 
            WHERE login = %s
            """,
            (login_data.login,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"User not found: {login_data.login}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )
        
        # Проверка пароля
        password_valid = verify_password(login_data.password, user['password_hash'])
        
        if not password_valid:
            logger.warning(f"Invalid password for user: {login_data.login}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )
        
        # Проверка активности
        if not user['is_active']:
            logger.warning(f"Inactive user: {login_data.login}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Учетная запись заблокирована"
            )
        
        # Обновляем время последнего входа
        try:
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user['id'],)
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"Could not update last_login: {e}")
            # Не критическая ошибка, продолжаем
        
        # Создание токенов
        access_token = create_token(
            {
                "sub": str(user['id']),
                "login": user['login'],
                "role_id": user['role_id'],
                "type": "access"
            },
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        refresh_token = create_token(
            {
                "sub": str(user['id']),
                "login": user['login'],
                "type": "refresh"
            },
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        )
        
        # Сохраняем refresh токен
        try:
            save_refresh_token(user['id'], refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS)
        except Exception as e:
            logger.error(f"Error saving refresh token: {e}")
            # Не критическая ошибка, продолжаем
        
        logger.info(f"User logged in successfully: {login_data.login}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        logger.error(traceback.format_exc())
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/api/auth/me", response_model=UserResponse, tags=["Auth"])
def get_me(token: str = Depends(oauth2_scheme)):
    """Получение информации о текущем пользователе"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не предоставлен"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT u.id, u.login, u.email, u.role_id, r.name as role_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.id = %s
            """,
            (payload.get("sub"),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return {
            "id": user['id'],
            "login": user['login'],
            "email": user.get('email'),
            "role_id": user['role_id']
        }
    
    finally:
        cursor.close()
        conn.close()


@router.post("/api/auth/logout", tags=["Auth"])
def logout(token: str = Depends(oauth2_scheme)):
    """Выход из системы"""
    if token:
        payload = decode_token(token)
        if payload:
            blacklist_token(token, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {"message": "Выход успешен"}