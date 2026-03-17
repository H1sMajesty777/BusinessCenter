# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, status
from api.database import get_db
from api.models.user import UserCreate, UserUpdate, User
from api.security import hash_password, verify_password
from api.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter()

# ─── CREATE ──────────────────────────────────────────────────
@router.post('/api/users', status_code=201, tags=['Пользователи'])
def create_user(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверка на уникальный login
    cursor.execute('SELECT id FROM users WHERE login = %s', (user.login,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail='Логин уже занят')
    
    # Проверка на уникальный email
    cursor.execute('SELECT id FROM users WHERE email = %s', (user.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail='Email уже зарегистрирован')
    
    # Хешируем пароль
    password_hash = hash_password(user.password)
    
    cursor.execute("""
        INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, login, email, phone, full_name, role_id, created_at, is_active
    """, (user.login, password_hash, user.email, user.phone, user.full_name, user.role_id, user.is_active))
    
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        'id': row[0],
        'login': row[1],
        'email': row[2],
        'phone': row[3],
        'full_name': row[4],
        'role_id': row[5],
        'created_at': str(row[6]),
        'is_active': row[7],
        'message': 'Пользователь создан'
    }

# ─── READ ALL ────────────────────────────────────────────────
@router.get('/api/users', tags=['Пользователи'])
def get_users(current_user: dict = Depends(get_current_active_user)):
    """Только для авторизованных пользователей"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, login, email, phone, full_name, role_id, created_at, is_active 
        FROM users ORDER BY id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [
        {
            'id': r[0], 'login': r[1], 'email': r[2], 'phone': r[3],
            'full_name': r[4], 'role_id': r[5], 'created_at': str(r[6]), 'is_active': r[7]
        }
        for r in rows
    ]

# ─── READ ONE ────────────────────────────────────────────────
@router.get('/api/users/{user_id}', tags=['Пользователи'])
def get_user(user_id: int, current_user: dict = Depends(get_current_active_user)):
    """Только для авторизованных пользователей"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, login, email, phone, full_name, role_id, created_at, is_active 
        FROM users WHERE id = %s
    """, (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    return {
        'id': row[0], 'login': row[1], 'email': row[2], 'phone': row[3],
        'full_name': row[4], 'role_id': row[5], 'created_at': str(row[6]), 'is_active': row[7]
    }

# ─── UPDATE ──────────────────────────────────────────────────
@router.put('/api/users/{user_id}', tags=['Пользователи'])
def update_user(
    user_id: int, 
    user: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Только для авторизованных пользователей (себя) или админа"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверка существования
    cursor.execute('SELECT id, role_id FROM users WHERE id = %s', (user_id,))
    existing = cursor.fetchone()
    if not existing:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # Проверка прав (можно редактировать только себя или если ты админ)
    if current_user.get('sub') != str(user_id) and current_user.get('role_id') != 1:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=403, detail='Недостаточно прав')
    
    data = user.model_dump(exclude_unset=True)
    if not 
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail='Нет данных для обновления')
    
    # Проверка на уникальный login если меняется
    if 'login' in data:
        cursor.execute('SELECT id FROM users WHERE login = %s AND id != %s', (data['login'], user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail='Логин уже занят')
    
    # Проверка на уникальный email если меняется
    if 'email' in data:
        cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (data['email'], user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail='Email уже зарегистрирован')
    
    # Хешируем пароль если есть
    if 'password' in data and data['password']:
        data['password_hash'] = hash_password(data['password'])
        del data['password']
    
    set_clause = ', '.join(f'{k} = %s' for k in data.keys())
    values = list(data.values()) + [user_id]
    
    cursor.execute(f'UPDATE users SET {set_clause} WHERE id = %s RETURNING id, login, email', values)
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {'id': row[0], 'login': row[1], 'email': row[2], 'message': 'Пользователь обновлён'}

# ─── DELETE ──────────────────────────────────────────────────
@router.delete('/api/users/{user_id}', tags=['Пользователи'])
def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """Только для администраторов"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Нельзя удалить самого себя
    if current_user.get('sub') == str(user_id):
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail='Нельзя удалить самого себя')
    
    cursor.execute('DELETE FROM users WHERE id = %s RETURNING id', (user_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {'message': f'Пользователь {user_id} удалён'}

# ─── МОЙ ПРОФИЛЬ ─────────────────────────────────────────────
@router.get('/api/users/me/profile', tags=['Пользователи'])
def get_my_profile(current_user: dict = Depends(get_current_active_user)):
    """Получить данные текущего пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, login, email, phone, full_name, role_id, created_at, is_active 
        FROM users WHERE id = %s
    """, (current_user.get('sub'),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    return {
        'id': row[0], 'login': row[1], 'email': row[2], 'phone': row[3],
        'full_name': row[4], 'role_id': row[5], 'created_at': str(row[6]), 'is_active': row[7]
    }

@router.put('/api/users/me/profile', tags=['Пользователи'])
def update_my_profile(
    user: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Обновить данные текущего пользователя"""
    user_id = int(current_user.get('sub'))
    
    # Запрещаем менять role_id и is_active через этот endpoint
    if user.role_id is not None or user.is_active is not None:
        raise HTTPException(status_code=400, detail='Нельзя изменить роль или статус через этот endpoint')
    
    # Вызываем обычный update
    conn = get_db()
    cursor = conn.cursor()
    
    data = user.model_dump(exclude_unset=True)
    if 'role_id' in 
        del data['role_id']
    if 'is_active' in 
        del data['is_active']
    
    if not 
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail='Нет данных для обновления')
    
    if 'password' in data and data['password']:
        data['password_hash'] = hash_password(data['password'])
        del data['password']
    
    set_clause = ', '.join(f'{k} = %s' for k in data.keys())
    values = list(data.values()) + [user_id]
    
    cursor.execute(f'UPDATE users SET {set_clause} WHERE id = %s RETURNING id, login, email', values)
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {'id': row[0], 'login': row[1], 'email': row[2], 'message': 'Профиль обновлён'}