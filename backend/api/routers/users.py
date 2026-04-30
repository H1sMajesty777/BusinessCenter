# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from api.database import get_db
from api.security import hash_password, verify_password, create_token, decode_token
from api.models.user import UserCreate, UserUpdate, UserResponse, Token
from api.rate_limiter import limiter, RATE_LIMITS
# from api.security import get_current_user_from_cookie as get_current_user
from api.security import get_current_user 

# Router с правильным префиксом
router = APIRouter(prefix="/api/users", tags=["Users"])
# security = HTTPBearer(auto_error=False)


# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     Получить текущего пользователя из JWT токена
    
#     """
#     if not credentials:
#         raise HTTPException(status_code=401, detail="Нет токена")
    
#     token = credentials.credentials
#     payload = decode_token(token)
    
#     if not payload:
#         raise HTTPException(status_code=401, detail="Неверный токен")
    
#     return payload


def require_admin(current_user: dict):
    """
    Проверка роли: только админ
    
    """
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit(RATE_LIMITS["register"])
def register_client(request: Request, user: UserCreate):
    """
    Регистрация нового пользователя
    
    Доступ: Все авторизованные
    """
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
            """INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP) 
               RETURNING id, login, email, phone, full_name, role_id, is_active, created_at""",
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
            id=row['id'],
            login=row['login'],
            email=row['email'],
            phone=row['phone'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/me", response_model=UserResponse)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_my_profile(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Просмотр своего профиля
    Доступ: Все авторизованные
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT id, login, email, phone, full_name, role_id, is_active, created_at 
               FROM users WHERE id = %s""",
            (current_user.get("sub"),)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return UserResponse(
            id=row['id'],
            login=row['login'],
            email=row['email'],
            phone=row['phone'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )
    finally:
        cursor.close()
        conn.close()


@router.put("/me", response_model=UserResponse)
@limiter.limit(RATE_LIMITS["authenticated"])
def update_my_profile(request: Request, user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    """
    Редактирование своего профиля
    Доступ: Все авторизованные
    """
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
        
        # Нельзя изменить роль и is_active через этот endpoint
        # Это может делать только админ через PUT /{user_id}
        
        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        params.append(current_user.get("sub"))
        
        cursor.execute(
            f"""UPDATE users SET {', '.join(updates)} 
                WHERE id = %s 
                RETURNING id, login, email, phone, full_name, role_id, is_active, created_at""",
            tuple(params)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        conn.commit()
        
        return UserResponse(
            id=row['id'],
            login=row['login'],
            email=row['email'],
            phone=row['phone'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )
    finally:
        cursor.close()
        conn.close()


@router.get("", response_model=List[UserResponse])
@limiter.limit(RATE_LIMITS["admin"])
def get_all_users(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Максимальное количество записей"),
    role_id: Optional[int] = Query(None, description="Фильтр по роли"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    current_user: dict = Depends(get_current_user)
):
    """
    Все пользователи — ТОЛЬКО АДМИН
    
    Доступ: Только админ 
    """
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        query = "SELECT id, login, email, phone, full_name, role_id, is_active, created_at FROM users WHERE 1=1"
        params = []
        
        if role_id is not None:
            query += " AND role_id = %s"
            params.append(role_id)
        
        if is_active is not None:
            query += " AND is_active = %s"
            params.append(is_active)
        
        query += " ORDER BY id LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            UserResponse(
                id=r['id'],
                login=r['login'],
                email=r['email'],
                phone=r['phone'],
                full_name=r['full_name'],
                role_id=r['role_id'],
                is_active=r['is_active'],
                created_at=r['created_at']
            )
            for r in rows
        ]
    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201, response_model=UserResponse)
@limiter.limit(RATE_LIMITS["admin"])
def create_user(request: Request, user: UserCreate, current_user: dict = Depends(get_current_user)):
    """
    Создание пользователя — ТОЛЬКО АДМИН
    
    Доступ: Только админ 
    """
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
            """INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP) 
               RETURNING id, login, email, phone, full_name, role_id, is_active, created_at""",
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
            id=row['id'],
            login=row['login'],
            email=row['email'],
            phone=row['phone'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_user(request: Request, user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Получение пользователя по ID
    Доступ: Админ или сам пользователь
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка прав доступа (админ или сам пользователь)
        if current_user.get("role_id") != 1:
            if str(current_user.get("sub")) != str(user_id):
                raise HTTPException(status_code=403, detail="Нет доступа к данным этого пользователя")
        
        cursor.execute(
            """SELECT id, login, email, phone, full_name, role_id, is_active, created_at 
               FROM users WHERE id = %s""",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return UserResponse(
            id=row['id'],
            login=row['login'],
            email=row['email'],
            phone=row['phone'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )
    finally:
        cursor.close()
        conn.close()


@router.put("/{user_id}", response_model=UserResponse)
@limiter.limit(RATE_LIMITS["admin"])
def update_user(
    request: Request,
    user_id: int, 
    user_update: UserUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """
    Обновление пользователя — ТОЛЬКО АДМИН
    Доступ: Только админ
    """
    require_admin(current_user)
    
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
        
        if user_update.role_id is not None:
            updates.append("role_id = %s")
            params.append(user_update.role_id)
        
        if user_update.is_active is not None:
            updates.append("is_active = %s")
            params.append(user_update.is_active)
        
        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        params.append(user_id)
        
        cursor.execute(
            f"""UPDATE users SET {', '.join(updates)} 
                WHERE id = %s 
                RETURNING id, login, email, phone, full_name, role_id, is_active, created_at""",
            tuple(params)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        conn.commit()
        
        return UserResponse(
            id=row['id'],
            login=row['login'],
            email=row['email'],
            phone=row['phone'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )
    finally:
        cursor.close()
        conn.close()


@router.delete("/{user_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["admin"])
def delete_user(request: Request, user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Удаление пользователя — ТОЛЬКО АДМИН

    """
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


@router.get("/stats/summary", response_model=dict)
@limiter.limit(RATE_LIMITS["admin"])
def get_users_stats(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Статистика пользователей
    Доступ: Только админ
    """
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Общее количество
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total = cursor.fetchone()['count']
        
        # Активные
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
        active = cursor.fetchone()['count']
        
        # Неактивные
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = FALSE")
        inactive = cursor.fetchone()['count']
        
        # По ролям
        cursor.execute("""
            SELECT r.name, COUNT(u.id) as count 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            GROUP BY r.name
        """)
        by_role = cursor.fetchall()
        
        return {
            "total_users": total,
            "active_users": active,
            "inactive_users": inactive,
            "by_role": [{"role_name": r['name'], "count": r['count']} for r in by_role]
        }
    finally:
        cursor.close()
        conn.close()

@router.get("/{user_id}/contacts", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_user_contacts(
    request: Request,
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Получение контактов пользователя (телефон, email)
    Доступ: Админ, Менеджер или сам пользователь
    """
    # Проверка прав
    if current_user.get("role_id") not in [1, 2]:  # админ или менеджер
        if str(current_user.get("sub")) != str(user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к контактам")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, login, email, phone, full_name FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return {
            "id": user['id'],
            "login": user['login'],
            "email": user['email'],
            "phone": user['phone'],
            "full_name": user['full_name']
        }
    finally:
        cursor.close()
        conn.close()