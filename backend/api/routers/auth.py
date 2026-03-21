# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional
import logging

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
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, login, password_hash, role_id, is_active FROM users WHERE login = %s",
            (login_data.login,)
        )
        user = cursor.fetchone()
        
        if not user or not verify_password(login_data.password, user[2]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )
        
        if not user[4]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Учетная запись заблокирована"
            )
        
        # Создание токенов
        access_token = create_token(
            {"sub": str(user[0]), "login": user[1], "role_id": user[3]},
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        refresh_token = create_token(
            {"sub": str(user[0]), "login": user[1]},
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        )
        
        save_refresh_token(user[0], refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    finally:
        cursor.close()
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
            "SELECT id, login, email, role_id FROM users WHERE id = %s",
            (payload.get("sub"),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return {
            "id": user[0],
            "login": user[1],
            "email": user[2],
            "role_id": user[3]
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