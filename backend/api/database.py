# -*- coding: utf-8 -*-
"""
Подключение к базам данных
PostgreSQL (Docker) + Redis (Docker)
"""

import psycopg  # ← psycopg v3
import redis
from api.config import settings

_redis_client = None


def get_db():
    """
    Подключение к PostgreSQL (Docker)
    
    Returns:
        psycopg.Connection: Объект подключения к базе данных
    """
    conn = psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME,
        connect_timeout=5
        # sslmode не нужен для localhost!
    )
    return conn


def get_redis():
    """
    Подключение к Redis (Docker)
    
    Returns:
        redis.Redis: Объект подключения к Redis
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    return _redis_client


def close_redis():
    """Закрыть подключение к Redis"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None