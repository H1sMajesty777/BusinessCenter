# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from api.database import get_db
from api.security import (
    hash_password,
    decode_token,
    is_token_blacklisted,
    verify_password
)
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ========== МОДЕЛИ ==========
class UserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None  # Убрал EmailStr чтобы не требовать email-validator
    role_id: int = Field(default=3, ge=1, le=10)  # 1=admin, 2=manager, 3=client


class UserResponse(BaseModel):
    id: int
    login: str
    email: Optional[str] = None
    role_id: int
    is_active: bool


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    role_id: Optional[int] = Field(None, ge=1, le=10)


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_current_user(token: str = Depends(oauth2_scheme)):
    """Получить текущего пользователя из JWT токена"""
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Токен отозван")
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload


def require_admin(current_user: dict):
    """Проверка что пользователь — админ"""
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только для администраторов")


def require_self_or_admin(current_user: dict, user_id: int):
    """Проверка что пользователь — админ или редактирует себя"""
    if current_user.get("role_id") != 1 and str(current_user.get("sub")) != str(user_id):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


# ========== ЭНДПОИНТЫ ==========

@router.post("/api/users", response_model=UserResponse, tags=["Users"], status_code=201)
def create_user(user: UserCreate):
    """Создание нового пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка уникальности логина и email
        cursor.execute(
            "SELECT id FROM users WHERE login = %s OR email = %s",
            (user_data.login, user_data.email)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Логин или email уже занят")
        
        # Создание пользователя
        hashed = hash_password(user_data.password)
        cursor.execute(
            """INSERT INTO users (login, password_hash, email, role_id, is_active)
               VALUES (%s, %s, %s, %s, TRUE)
               RETURNING id, login, email, role_id, is_active""",
            (user_data.login, hashed, user_data.email, user_data.role_id)
        )
        user = cursor.fetchone()
        conn.commit()
        
        logger.info(f"User created: {user_data.login}")
        return {"id": user[0], "login": user[1], "email": user[2], "role_id": user[3], "is_active": user[4]}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")
    finally:
        cursor.close()
        conn.close()


@router.get("/api/users", response_model=List[UserResponse], tags=["Users"])
def get_users(
    skip: int = 0,
    limit: int = 100,
    current: dict = Depends(get_current_user)
):
    """Получение списка пользователей (только для админов)"""
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, login, email, role_id, is_active FROM users ORDER BY id LIMIT %s OFFSET %s",
            (limit, skip)
        )
        users = cursor.fetchall()
        return [{"id": u[0], "login": u[1], "email": u[2], "role_id": u[3], "is_active": u[4]} for u in users]
    finally:
        cursor.close()
        conn.close()


@router.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(
    user_id: int,
    current: dict = Depends(get_current_user)
):
    """Получение информации о пользователе"""
    require_self_or_admin(current_user, user_id)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, login, email, role_id, is_active FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return {"id": user[0], "login": user[1], "email": user[2], "role_id": user[3], "is_active": user[4]}
    finally:
        cursor.close()
        conn.close()


@router.put("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user(
    user_id: int,
    user: UserUpdate,
    current: dict = Depends(get_current_user)
):
    """Обновление информации о пользователе"""
    require_self_or_admin(current_user, user_id)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка существования
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Сбор полей для обновления
        updates = []
        params = []
        
        if user_data.email is not None:
            updates.append("email = %s")
            params.append(user_data.email)
        
        if user_data.password is not None:
            updates.append("password_hash = %s")
            params.append(hash_password(user_data.password))
        
        if user_data.is_active is not None:
            require_admin(current_user)  # Только админ меняет статус
            updates.append("is_active = %s")
            params.append(user_data.is_active)
        
        if user_data.role_id is not None:
            require_admin(current_user)  # Только админ меняет роль
            updates.append("role_id = %s")
            params.append(user_data.role_id)
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING id, login, email, role_id, is_active"
            cursor.execute(query, params)
            user = cursor.fetchone()
            conn.commit()
            logger.info(f"User updated: {user[1]}")
            return {"id": user[0], "login": user[1], "email": user[2], "role_id": user[3], "is_active": user[4]}
        else:
            # Нет изменений — возвращаем текущие данные
            cursor.execute("SELECT id, login, email, role_id, is_active FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return {"id": user[0], "login": user[1], "email": user[2], "role_id": user[3], "is_active": user[4]}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении")
    finally:
        cursor.close()
        conn.close()


@router.delete("/api/users/{user_id}", tags=["Users"])
def delete_user(
    user_id: int,
    current: dict = Depends(get_current_user)
):
    """Удаление пользователя (только для админов)"""
    require_admin(current_user)
    
    # Нельзя удалить себя
    if str(current_user.get("sub")) == str(user_id):
        raise HTTPException(status_code=400, detail="Нельзя удалить свою учетную запись")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        conn.commit()
        logger.info(f"User deleted: {user_id}")
        return {"message": "Пользователь успешно удален"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при удалении")
    finally:
        cursor.close()
        conn.close()