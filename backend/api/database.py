# -*- coding: utf-8 -*-
"""
Подключение к PostgreSQL и Redis с полной поддержкой UTF-8
"""

import psycopg
from psycopg.rows import dict_row  # ← Для удобного доступа к колонкам по имени
import redis
from api.config import settings

_redis_client = None


def get_db():
    """
    Подключение к PostgreSQL с гарантированной поддержкой UTF-8
    
    Returns:
        psycopg.Connection: Объект подключения с UTF-8 кодировкой
    """
    conn = psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME,
        # ✅ КЛЮЧЕВЫЕ ПАРАМЕТРЫ ДЛЯ UTF-8:
        client_encoding='UTF8',              # Кодировка клиента
        options='-c client_encoding=UTF8',   # Принудительно для сессии
        connect_timeout=5
    )
    # ✅ Возвращаем строки как словари (удобнее: row['description'])
    conn.row_factory = dict_row
    return conn


def get_redis():
    """
    Подключение к Redis с поддержкой UTF-8
    
    Returns:
        redis.Redis: Объект подключения к Redis
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            # ✅ Явно указываем кодировку:
            encoding='utf-8',
            decode_responses=True  # Автоматически декодирует bytes → str
        )
    return _redis_client


def close_redis():
    """Закрыть подключение к Redis"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None