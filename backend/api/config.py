# -*- coding: utf-8 -*-
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """
    Настройки приложения
    Все переменные окружения могут быть переопределены через .env файл
    """
    
    # JWT настройки
    JWT_SECRET_KEY: str = Field(
        default="super-secret-key-change-me-in-production",
        min_length=32,
        description="Секретный ключ для JWT (минимум 32 символа в production)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Алгоритм шифрования JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Время жизни access токена в минутах (1-1440)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Время жизни refresh токена в днях (1-30)"
    )
    
    # PostgreSQL настройки
    DB_HOST: str = Field(
        default="localhost",
        description="Хост PostgreSQL"
    )
    DB_PORT: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="Порт PostgreSQL"
    )
    DB_USER: str = Field(
        default="postgres",
        description="Пользователь PostgreSQL"
    )
    DB_PASSWORD: str = Field(
        default="admin",
        description="Пароль PostgreSQL"
    )
    DB_NAME: str = Field(
        default="project",
        description="Имя базы данных PostgreSQL"
    )
    
    # Redis настройки
    REDIS_HOST: str = Field(
        default="localhost",
        description="Хост Redis"
    )
    REDIS_PORT: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Порт Redis"
    )
    REDIS_DB: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Номер базы данных Redis"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Пароль Redis (если требуется)"
    )
    
    # Дополнительные настройки
    ENVIRONMENT: str = Field(
        default="development",
        pattern="^(development|staging|production)$",
        description="Окружение: development, staging, production"
    )
    DEBUG: bool = Field(
        default=True,
        description="Режим отладки"
    )
    
    # Настройки для Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Игнорировать лишние переменные
    )
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Проверка секретного ключа JWT"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY должен содержать минимум 32 символа")
        return v
    
    @property
    def database_url(self) -> str:
        """Формирует URL для подключения к PostgreSQL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def async_database_url(self) -> str:
        """Формирует асинхронный URL для подключения к PostgreSQL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_url(self) -> str:
        """Формирует URL для подключения к Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def is_production(self) -> bool:
        """Проверка, является ли окружение production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Проверка, является ли окружение development"""
        return self.ENVIRONMENT == "development"


# Создаем экземпляр настроек
settings = Settings()


# Функция для получения настроек (для Dependency Injection)
def get_settings() -> Settings:
    """Возвращает настройки приложения"""
    return settings