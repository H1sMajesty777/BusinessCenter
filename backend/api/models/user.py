from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ========== ДЛЯ СОЗДАНИЯ ==========
class UserCreate(BaseModel):
    """Создание нового пользователя"""
    login: str = Field(..., min_length=3, max_length=50, description="Логин")
    password: str = Field(..., min_length=6, max_length=100, description="Пароль")
    email: str = Field(..., description="Email")
    phone: Optional[str] = Field(None, max_length=20, description="Телефон")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    role_id: int = Field(default=3, ge=1, le=3, description="ID роли (1=admin, 2=manager, 3=client)")
    is_active: bool = Field(default=True, description="Активен ли пользователь")


# ========== ДЛЯ ОБНОВЛЕНИЯ ==========
class UserUpdate(BaseModel):
    """Обновление пользователя (все поля необязательны)"""
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, max_length=20, description="Телефон")
    full_name: Optional[str] = Field(None, max_length=100, description="ФИО")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="Новый пароль")
    role_id: Optional[int] = Field(None, ge=1, le=3, description="ID роли")
    is_active: Optional[bool] = Field(None, description="Активен ли пользователь")


# ========== ДЛЯ ОТВЕТА (RESPONSE) ==========
class UserResponse(BaseModel):
    """Ответ с данными пользователя"""
    id: int
    login: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ========== ДЛЯ АВТОРИЗАЦИИ ==========
class UserLogin(BaseModel):
    """Вход в систему"""
    login: str = Field(..., description="Логин")
    password: str = Field(..., description="Пароль")


class Token(BaseModel):
    """JWT токен"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class TokenData(BaseModel):
    """Данные из токена"""
    sub: Optional[str] = None
    role_id: Optional[int] = None
    exp: Optional[datetime] = None


# чтобы auth.py работал!
LoginRequest = UserLogin