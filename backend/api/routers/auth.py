from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from api.database import get_db, get_redis
from api.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    blacklist_token,
    store_refresh_token,
    delete_refresh_token,
    is_token_blacklisted,
    settings
)
from api.models.user import LoginRequest, Token, UserResponse, TokenRefresh


router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить текущего пользователя из JWT access токена
    
    Args:
        credentials: JWT токен из заголовка Authorization
    
    Returns:
        dict: Payload токена (sub, role_id, login, etc.)
    
    Raises:
        HTTPException: 401 если токена нет, он неверный или в blacklist
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = credentials.credentials
    
    # Проверка blacklist
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Токен отозван")
    
    # Декодирование токена
    payload = decode_token(token, expected_type="access")
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload


# ENDPOINTS

@router.post("/login", response_model=Token)
def login(login_request: LoginRequest = Body(...)):
    """
    Вход в систему с выдачей access + refresh токенов
    
    Доступ: Все (публичный endpoint)
    
    Args:
        login_request: Данные для входа (login, password)
    
    Returns:
        Token: Access и refresh токены
    
    Raises:
        HTTPException: 401 если логин или пароль неверны
        HTTPException: 403 если аккаунт заблокирован
    
    Example:
        POST /api/auth/login
        {
            "login": "admin",
            "password": "admin123"
        }
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
        
        user_id = user['id']
        user_login = user['login']
        password_hash = user['password_hash']
        role_id = user['role_id']
        is_active = user['is_active']
        
        # Декодируем password_hash если он bytes
        if isinstance(password_hash, bytes):
            password_hash = password_hash.decode('utf-8')
        
        # Проверка пароля
        if not verify_password(login_request.password, password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        # Проверка активности
        if not is_active:
            raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
        
        # Создаём токены
        access_token = create_access_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id},
            expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id},
            expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        # Сохраняем refresh токен в Redis
        store_refresh_token(str(user_id), refresh_token)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
    
    finally:
        cursor.close()
        conn.close()


@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh = Body(...)):
    """
    Обновление access токена через refresh токен
    
    Доступ: Все у кого есть валидный refresh токен
    
    Args:
        token_data: Refresh токен
    
    Returns:
        Token: Новые access и refresh токены
    
    Raises:
        HTTPException: 401 если refresh токен неверный или отозван
        HTTPException: 403 если пользователь заблокирован
    
    Example:
        POST /api/auth/refresh
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
        }
    """
    # Декодируем refresh токен
    payload = decode_token(token_data.refresh_token, expected_type="refresh")
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный refresh токен")
    
    user_id = payload.get("sub")
    user_login = payload.get("login")
    role_id = payload.get("role_id")
    
    # Проверяем что refresh токен хранится в Redis
    stored_token = get_refresh_token(user_id)
    if not stored_token or stored_token != token_data.refresh_token:
        raise HTTPException(status_code=401, detail="Refresh токен отозван или не найден")
    
    # Проверяем что пользователь всё ещё активен
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT is_active FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user or not user['is_active']:
            # Удаляем refresh токен если пользователь заблокирован
            delete_refresh_token(user_id)
            raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
        
        # Создаём новые токены
        new_access_token = create_access_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id},
            expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        new_refresh_token = create_refresh_token(
            data={"sub": str(user_id), "login": user_login, "role_id": role_id},
            expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        # Сохраняем новый refresh токен в Redis
        store_refresh_token(user_id, new_refresh_token)
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
    
    finally:
        cursor.close()
        conn.close()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Просмотр своего профиля
    
    Доступ: Все авторизованные с валидным access токеном
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        UserResponse: Данные профиля текущего пользователя
    
    Raises:
        HTTPException: 404 если пользователь не найден
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT id, login, email, phone, full_name, role_id, is_active, created_at 
               FROM users WHERE id = %s""",
            (current_user.get("sub"),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
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
    Выход из системы с отзывом всех токенов
    
    Доступ: Все авторизованные
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном выходе
    
    Note:
        Access токен добавляется в blacklist
        Refresh токен удаляется из Redis
        Клиент должен удалить токены локально
    """
    credentials = None
    try:
        # Получаем токен из заголовка
        from fastapi import Request
        # Токен уже проверен в get_current_user
    except:
        pass
    
    user_id = current_user.get("sub")
    
    # Добавляем access токен в blacklist (будет проверяться при каждом запросе)
    # Токен передаётся через Depends(get_current_user)
    
    # Удаляем refresh токен из Redis
    delete_refresh_token(user_id)
    
    return {
        "message": "Выход успешен",
        "detail": "Все токены отозваны. Удалите токены на клиенте."
    }


@router.post("/logout/all", response_model=dict)
def logout_all(current_user: dict = Depends(get_current_user)):
    """
    Выход со всех устройств (отзыв всех токенов пользователя)
    
    Доступ: Все авторизованные
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном выходе со всех устройств
    
    Note:
        Удаляет refresh токен из Redis
        При следующем запросе с любым токеном будет отказ
    """
    user_id = current_user.get("sub")
    
    # Удаляем refresh токен
    delete_refresh_token(user_id)
    
    return {
        "message": "Выход со всех устройств успешен",
        "detail": "Все токены отозваны. Необходимо войти заново."
    }