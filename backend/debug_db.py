# backend/debug_db.py
from api.config import settings
from api.database import get_db

print("🔍 Настройки подключения:")
print(f"DB_HOST: {settings.DB_HOST}")
print(f"DB_PORT: {settings.DB_PORT}")
print(f"DB_NAME: {settings.DB_NAME}")

print("\n🔍 Пользователи в базе:")
conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT id, login, email, created_at FROM users ORDER BY id")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} | {row[2]} | {row[3]}")
conn.close()