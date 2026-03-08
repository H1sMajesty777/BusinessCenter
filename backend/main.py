# -*- coding: utf-8 -*-
import psycopg
from psycopg.sql import SQL, Identifier

conn = psycopg.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='admin',
    dbname='project',
    autocommit=True
)

cursor = conn.cursor()

# Получаем все таблицы
cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' ORDER BY table_name
""")
tables = cursor.fetchall()

print('\n' + '='*50)
print('📊 БАЗА ДАННЫХ "project"')
print('='*50)

for table in tables:
    table_name = table[0]
    cursor.execute(SQL("SELECT COUNT(*) FROM {}").format(Identifier(table_name)))
    count = cursor.fetchone()[0]
    print(f'✅ {table_name}: {count} записей')

print('='*50)

# Пример данных из offices
print('\n🏢 ОФИСЫ (пример):')
cursor.execute("""
    SELECT office_number, floor, area_sqm, price_per_month 
    FROM offices LIMIT 5
""")
for row in cursor.fetchall():
    print(f'   {row[0]} | Этаж {row[1]} | {row[2]} м² | {row[3]:.0f} ₽/мес')

print('='*50 + '\n')

cursor.close()
conn.close()
print('✅ Подключение успешно!\n')