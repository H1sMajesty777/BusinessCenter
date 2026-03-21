# -*- coding: utf-8 -*-
import psycopg
import redis
from api.config import settings

_redis_client = None

def get_db():
    """Подключение к PostgreSQL"""
    return psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME
    )

def get_redis():
    """Подключение к Redis"""
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