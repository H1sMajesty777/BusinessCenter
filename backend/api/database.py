import psycopg
from psycopg.rows import dict_row
import redis
from api.config import settings

_redis_client = None


def get_db():
    """
    Подключение к PostgreSQL
    """
    conn = psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME,
        client_encoding='UTF8',
        options='-c client_encoding=UTF8',   # Принудительно для сессии
        connect_timeout=5
    )
    # строки как словари (row['description'])
    conn.row_factory = dict_row
    return conn


def get_redis():
    """
    Подключение к Redis
    
    """
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                encoding='utf-8',
                decode_responses=True,  # Автоматически декодирует bytes → str
                socket_connect_timeout=5
            )
            # Проверка подключения
            _redis_client.ping()
        except redis.ConnectionError as e:
            raise redis.ConnectionError(f"Не удалось подключиться к Redis: {e}")
    return _redis_client

def check_redis_health() -> dict:
    """Проверка здоровья Redis с информацией о персистентности"""
    try:
        redis_client = get_redis()
        
        # Проверяем конфигурацию персистентности
        aof_enabled = redis_client.config_get('appendonly')
        aof_fsync = redis_client.config_get('appendfsync')
        
        return {
            "status": "healthy",
            "persistence": {
                "aof_enabled": aof_enabled.get('appendonly') == 'yes',
                "aof_fsync": aof_fsync.get('appendfsync', 'everysec'),
                "rdb_enabled": True
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def close_redis():
    """Закрыть подключение к Redis"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None