import psycopg
import os

def get_db():
    """Подключение к базе данных"""
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        dbname=os.getenv('DB_NAME', 'project')
    )