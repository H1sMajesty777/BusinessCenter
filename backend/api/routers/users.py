# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
import logging

from api.database import get_db
from api.security import (
    hash_password,
    decode_token,
    is_token_blacklisted,
    get_current_user
)

logger = logging.getLogger(__name__)

router = APIRouter()


class UserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    role_id: int = Field(default=2, ge=1, le=10)  # 1 - admin, 2 - user, etc.


class UserResponse(BaseModel):
    id: int
    login: str
    email: Optional[str] = None
    role_id: int
    is_active: bool


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    role_id: Optional[int] = Field(None, ge=1, le=10)


@router.post("/api/users", response_model=UserResponse, tags=["Users"])
def create_user(user_data: UserCreate):
    """Создание нового пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка существования пользователя
        cursor.execute(
            "SELECT id FROM users WHERE login = %s",
            (user_data.login,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким логином уже существует"
            )
        
        # Хэширование пароля
        hashed_password = hash_password(user_data.password)
        
        # Создание пользователя
        cursor.execute(
            """
            INSERT INTO users (login, password_hash, email, role_id, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            RETURNING id, login, email, role_id, is_active
            """,
            (user_data.login, hashed_password, user_data.email, user_data.role_id)
        )
        
        user = cursor.fetchone()
        conn.commit()
        
        logger.info(f"User created: {user_data.login}")
        
        return {
            "id": user[0],
            "login": user[1],
            "email": user[2],
            "role_id": user[3],
            "is_active": user[4]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании пользователя"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/api/users", response_model=List[UserResponse], tags=["Users"])
def get_users(
    skip: int = 0,
    limit: int = 100,
    token: Optional[str] = None
):
    """Получение списка пользователей (только для админов)"""
    # Проверка авторизации
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )
    
    # Проверка прав (только админ)
    if current_user.get("role_id") != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT id, login, email, role_id, is_active
            FROM users
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            (limit, skip)
        )
        
        users = cursor.fetchall()
        
        return [
            {
                "id": user[0],
                "login": user[1],
                "email": user[2],
                "role_id": user[3],
                "is_active": user[4]
            }
            for user in users
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(
    user_id: int,
    token: Optional[str] = None
):
    """Получение информации о пользователе"""
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )
    
    # Проверка прав (админ или сам пользователь)
    if current_user.get("role_id") != 1 and str(current_user.get("sub")) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT id, login, email, role_id, is_active
            FROM users
            WHERE id = %s
            """,
            (user_id,)
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
            "role_id": user[3],
            "is_active": user[4]
        }
    
    finally:
        cursor.close()
        conn.close()


@router.put("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user(
    user_id: int,
    user_data: UserUpdate,
    token: Optional[str] = None
):
    """Обновление информации о пользователе"""
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )
    
    # Проверка прав (админ или сам пользователь)
    if current_user.get("role_id") != 1 and str(current_user.get("sub")) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка существования пользователя
        cursor.execute(
            "SELECT id FROM users WHERE id = %s",
            (user_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Формирование запроса на обновление
        update_fields = []
        params = []
        
        if user_data.email is not None:
            update_fields.append("email = %s")
            params.append(user_data.email)
        
        if user_data.password is not None:
            update_fields.append("password_hash = %s")
            params.append(hash_password(user_data.password))
        
        if user_data.is_active is not None:
            # Только админ может менять статус
            if current_user.get("role_id") != 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для изменения статуса"
                )
            update_fields.append("is_active = %s")
            params.append(user_data.is_active)
        
        if user_data.role_id is not None:
            # Только админ может менять роль
            if current_user.get("role_id") != 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для изменения роли"
                )
            update_fields.append("role_id = %s")
            params.append(user_data.role_id)
        
        if update_fields:
            params.append(user_id)
            query = f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, login, email, role_id, is_active
            """
            
            cursor.execute(query, params)
            user = cursor.fetchone()
            conn.commit()
            
            logger.info(f"User updated: {user[1]}")
            
            return {
                "id": user[0],
                "login": user[1],
                "email": user[2],
                "role_id": user[3],
                "is_active": user[4]
            }
        else:
            # Если нет полей для обновления, возвращаем текущие данные
            cursor.execute(
                "SELECT id, login, email, role_id, is_active FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            
            return {
                "id": user[0],
                "login": user[1],
                "email": user[2],
                "role_id": user[3],
                "is_active": user[4]
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении пользователя"
        )
    finally:
        cursor.close()
        conn.close()


@router.delete("/api/users/{user_id}", tags=["Users"])
def delete_user(
    user_id: int,
    token: Optional[str] = None
):
    """Удаление пользователя (только для админов)"""
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )
    
    # Проверка прав (только админ)
    if current_user.get("role_id") != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Нельзя удалить самого себя
        if str(current_user.get("sub")) == str(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить свою учетную запись"
            )
        
        cursor.execute(
            "DELETE FROM users WHERE id = %s RETURNING id",
            (user_id,)
        )
        
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        conn.commit()
        logger.info(f"User deleted: {user_id}")
        
        return {"message": "Пользователь успешно удален"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя"
        )
    finally:
        cursor.close()
        conn.close()