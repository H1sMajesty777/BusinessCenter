from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from api.database import get_db
from api.security import verify_password, create_token, decode_token
from api.models.user import LoginRequest, Token, UserResponse


router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить текущего пользователя из JWT токена
    
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload


# ENDPOINTS


@router.post("/login", response_model=Token)
def login(login_request: LoginRequest = Body(...)):
    """
    Вход в систему
    Доступ: Все 
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Поиск пользователя по логину
        cursor.execute(
            """SELECT id, login, password_hash, role_id, is_active 
               FROM users WHERE login = %s""",
            (login_request.login,)
        )
        user = cursor.fetchone()
        
        # Проверка существования
        if not user:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        # доступ через ключи словаря (dict_row)
        user_id = user['id']
        user_login = user['login']
        password_hash = user['password_hash']
        role_id = user['role_id']
        is_active = user['is_active']
        
        # декодируем password_hash если он bytes
        if isinstance(password_hash, bytes):
            password_hash = password_hash.decode('utf-8')
        
        # Проверка пароля
        if not verify_password(login_request.password, password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        # Проверка активности
        if not is_active:
            raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
        
        # Создание токена
        access_token = create_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id},
            expire_minutes=30
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800
        )
    
    finally:
        cursor.close()
        conn.close()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Просмотр своего профиля
    
    Доступ: Все авторизованные
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        UserResponse: Данные профиля текущего пользователя
    
    Raises:
        HTTPException: 404 если пользователь не найден
        HTTPException: 500 если ошибка при получении
    
    Example:
        GET /api/auth/me
        Authorization: Bearer <token>
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # ✅ ИСПРАВЛЕНО: добавлен created_at в SELECT
        cursor.execute(
            """SELECT id, login, email, phone, full_name, role_id, is_active, created_at 
               FROM users WHERE id = %s""",
            (current_user.get("sub"),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # ✅ ИСПРАВЛЕНО: доступ через ключи словаря (dict_row)
        return UserResponse(
            id=user['id'],
            login=user['login'],
            email=user['email'],
            phone=user['phone'],
            full_name=user['full_name'],
            role_id=user['role_id'],
            is_active=user['is_active'],
            created_at=user['created_at']
        )
    
    finally:
        cursor.close()
        conn.close()


@router.post("/logout", response_model=dict)
def logout(current_user: dict = Depends(get_current_user)):
    """
    Выход из системы
    
    Доступ: Все авторизованные
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном выходе
    
    Note:
        JWT токены не могут быть действительно "отозваны" на сервере.
        Клиент должен удалить токен локально.
        Для полноценного logout нужна система blacklist токенов (Redis).
    
    Example:
        POST /api/auth/logout
        Authorization: Bearer <token>
    """
    # ✅ В реальной системе здесь можно добавить токен в blacklist (Redis)
    # Например: redis_client.setex(f"blacklist:{token}", expire_time, "1")
    
    return {"message": "Выход успешен", "detail": "Удалите токен на клиенте"}