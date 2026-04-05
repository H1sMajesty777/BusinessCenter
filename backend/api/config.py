# backend/api/config.py
# -*- coding: utf-8 -*-
"""
Настройки приложения Business Center
Подключение к PostgreSQL и Redis
"""

import secrets
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ValidationError


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # ===================================================================
    # JWT НАСТРОЙКИ (ОБЯЗАТЕЛЬНО из .env!)
    # ===================================================================
    
    JWT_SECRET_KEY: str = Field(
        default="",
        description="Секретный ключ для JWT - ОБЯЗАТЕЛЬНО задать в .env!"
    )
    
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Алгоритм шифрования JWT"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Время жизни access токена в минутах"
    )
    
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Время жизни refresh токена в днях"
    )
    
    # ===================================================================
    # POSTGRESQL НАСТРОЙКИ
    # ===================================================================
    
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: str = Field(default="admin")
    DB_NAME: str = Field(default="project")
    
    # ===================================================================
    # REDIS НАСТРОЙКИ
    # ===================================================================
    
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    
    # ===================================================================
    # HTTPS И БЕЗОПАСНОСТЬ
    # ===================================================================
    
    SECURE_COOKIES: bool = Field(
        default=False,
        description="Использовать Secure флаг для Cookie (только при HTTPS)"
    )
    
    BEHIND_PROXY: bool = Field(
        default=False,
        description="За прокси (Nginx) - доверять X-Forwarded-* заголовкам"
    )
    
    # ===================================================================
    # COOKIE НАСТРОЙКИ
    # ===================================================================
    
    COOKIE_HTTPONLY: bool = Field(
        default=True,
        description="HttpOnly флаг - защита от XSS"
    )
    
    COOKIE_SAMESITE: str = Field(
        default="lax",
        description="SameSite флаг: lax, strict, none"
    )
    
    # ===================================================================
    # ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
    # ===================================================================
    
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    # ===================================================================
    # PYDANTIC V2 CONFIG
    # ===================================================================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ===================================================================
    # ВАЛИДАТОРЫ
    # ===================================================================
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Проверка секретного ключа JWT"""
        if not v or v == "":
            if cls._is_production():
                raise ValueError(
                    "JWT_SECRET_KEY не задан! Это КРИТИЧЕСКАЯ ошибка безопасности.\n"
                    "Сгенерируйте ключ: python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
                    "И добавьте в файл .env: JWT_SECRET_KEY=ваш_сгенерированный_ключ"
                )
            else:
                import warnings
                temp_key = secrets.token_urlsafe(32)
                warnings.warn(
                    f"ВНИМАНИЕ: JWT_SECRET_KEY не задан! Используется ВРЕМЕННЫЙ ключ.\n"
                    f"Для production ОБЯЗАТЕЛЬНО задайте постоянный ключ в .env!\n"
                    f"Временный ключ: {temp_key}",
                    RuntimeWarning
                )
                return temp_key
        
        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET_KEY должен содержать минимум 32 символа. "
                f"Сейчас: {len(v)} символов"
            )
        
        default_secrets = [
            "super-secret-key-change-me-in-production",
            "your-secret-key-change-this",
            "secret",
            "password"
        ]
        
        if v.lower() in default_secrets:
            raise ValueError(
                "Используется НЕНАДЁЖНЫЙ секретный ключ! "
                "Сгенерируйте уникальный ключ через secrets.token_urlsafe(32)"
            )
        
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Проверка окружения"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT должен быть одним из: {allowed}")
        return v
    
    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_samesite(cls, v: str) -> str:
        """Проверка SameSite значения"""
        allowed = ["lax", "strict", "none"]
        if v.lower() not in allowed:
            raise ValueError(f"COOKIE_SAMESITE должен быть одним из: {allowed}")
        return v.lower()
    
    # ===================================================================
    # ПРИВАТНЫЕ МЕТОДЫ
    # ===================================================================
    
    @classmethod
    def _is_production(cls) -> bool:
        """Проверка production режима"""
        try:
            import os
            env = os.getenv("ENVIRONMENT", "development")
            return env == "production"
        except Exception:
            return False
    
    # ===================================================================
    # СВОЙСТВА (PROPERTIES)
    # ===================================================================
    
    @property
    def database_url(self) -> str:
        """URL для подключения к PostgreSQL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_url(self) -> str:
        """URL для подключения к Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def is_production(self) -> bool:
        """Production ли окружение"""
        return self.ENVIRONMENT == "production"
    
    @property
    def cookie_secure(self) -> bool:
        """Secure флаг для Cookie - только в production с HTTPS"""
        return self.is_production and self.SECURE_COOKIES


# ===================================================================
# ИНИЦИАЛИЗАЦИЯ С ПРОВЕРКОЙ
# ===================================================================

try:
    settings = Settings()
    print(f"Конфигурация загружена из .env (окружение: {settings.ENVIRONMENT})")
    
    if settings.JWT_SECRET_KEY:
        secret_preview = settings.JWT_SECRET_KEY[:8] + "..." + settings.JWT_SECRET_KEY[-4:]
        print(f"JWT секрет загружен: {secret_preview} (длина: {len(settings.JWT_SECRET_KEY)} симв.)")
    
    print(f"Secure cookies: {settings.cookie_secure}")
    print(f"HttpOnly: {settings.COOKIE_HTTPONLY}")
    print(f"SameSite: {settings.COOKIE_SAMESITE}")
    print(f"Behind proxy: {settings.BEHIND_PROXY}")
    
except ValidationError as e:
    print("\n" + "="*60)
    print("ОШИБКА КОНФИГУРАЦИИ!")
    print("="*60)
    print(str(e))
    print("\n📝 Решение:")
    print("1. Создайте файл .env в корне проекта")
    print("2. Добавьте в него:")
    print("   JWT_SECRET_KEY=ваш_уникальный_ключ")
    print("3. Сгенерировать ключ можно командой:")
    print("   python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
    print("="*60)
    raise


def get_settings() -> Settings:
    """Возвращает настройки приложения"""
    return settings