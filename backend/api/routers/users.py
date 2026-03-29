# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from api.database import get_db
from api.security import hash_password, verify_password, create_token, decode_token
from api.models.user import UserCreate, UserUpdate, UserResponse, Token

router = APIRouter(prefix="/api/users", tags=["Users"])
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить текущего пользователя из токена"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload


def require_admin(current_user: dict):
    """Проверка роли: только админ"""
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")


@router.post("/register", response_model=UserResponse, status_code=201)
def register_client(user: UserCreate):
    """Регистрация — ТОЛЬКО КЛИЕНТ (role_id=3)"""
    if user.role_id != 3:
        raise HTTPException(status_code=403, detail="Только регистрация клиентов")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка на существующего пользователя
        cursor.execute(
            "SELECT id FROM users WHERE login = %s OR email = %s",
            (user.login, user.email)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Логин или email уже занят")
        
        # Создание пользователя
        cursor.execute(
            """INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) 
               RETURNING id, login, email, phone, full_name, role_id, is_active""",
            (
                user.login,
                hash_password(user.password),
                user.email,
                user.phone,
                user.full_name,
                user.role_id,
                user.is_active
            )
        )
        row = cursor.fetchone()
        conn.commit()
        
        return UserResponse(
            id=row[0],
            login=row[1],
            email=row[2],
            phone=row[3],
            full_name=row[4],
            role_id=row[5],
            is_active=row[6]
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Просмотр своего профиля"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, login, email, phone, full_name, role_id, is_active FROM users WHERE id = %s",
            (current_user.get("sub"),)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return UserResponse(
            id=row[0],
            login=row[1],
            email=row[2],
            phone=row[3],
            full_name=row[4],
            role_id=row[5],
            is_active=row[6]
        )
    finally:
        cursor.close()
        conn.close()


@router.put("/me", response_model=UserResponse)
def update_my_profile(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Редактирование своего профиля"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if user_update.email is not None:
            updates.append("email = %s")
            params.append(user_update.email)
        
        if user_update.phone is not None:
            updates.append("phone = %s")
            params.append(user_update.phone)
        
        if user_update.full_name is not None:
            updates.append("full_name = %s")
            params.append(user_update.full_name)
        
        if user_update.password is not None:
            updates.append("password_hash = %s")
            params.append(hash_password(user_update.password))
        
        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        params.append(current_user.get("sub"))
        
        cursor.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING id, login, email, phone, full_name, role_id, is_active",
            tuple(params)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        conn.commit()
        
        return UserResponse(
            id=row[0],
            login=row[1],
            email=row[2],
            phone=row[3],
            full_name=row[4],
            role_id=row[5],
            is_active=row[6]
        )
    finally:
        cursor.close()
        conn.close()


@router.get("", response_model=List[UserResponse])
def get_all_users(current_user: dict = Depends(get_current_user)):
    """Все пользователи — ТОЛЬКО АДМИН"""
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, login, email, phone, full_name, role_id, is_active FROM users ORDER BY id"
        )
        rows = cursor.fetchall()
        
        return [
            UserResponse(
                id=r[0],
                login=r[1],
                email=r[2],
                phone=r[3],
                full_name=r[4],
                role_id=r[5],
                is_active=r[6]
            )
            for r in rows
        ]
    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201, response_model=UserResponse)
def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)):
    """Создание пользователя — ТОЛЬКО АДМИН"""
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка на существующего
        cursor.execute(
            "SELECT id FROM users WHERE login = %s OR email = %s",
            (user.login, user.email)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Логин или email уже занят")
        
        # Создание
        cursor.execute(
            """INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) 
               RETURNING id, login, email, phone, full_name, role_id, is_active""",
            (
                user.login,
                hash_password(user.password),
                user.email,
                user.phone,
                user.full_name,
                user.role_id,
                user.is_active
            )
        )
        row = cursor.fetchone()
        conn.commit()
        
        return UserResponse(
            id=row[0],
            login=row[1],
            email=row[2],
            phone=row[3],
            full_name=row[4],
            role_id=row[5],
            is_active=row[6]
        )
    finally:
        cursor.close()
        conn.close()


@router.delete("/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Удаление пользователя — ТОЛЬКО АДМИН"""
    require_admin(current_user)
    
    # Нельзя удалить себя
    if str(current_user.get("sub")) == str(user_id):
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        conn.commit()
        
        return {"message": f"Пользователь {user_id} удалён"}
    finally:
        cursor.close()
        conn.close()