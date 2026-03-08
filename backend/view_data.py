# -*- coding: utf-8 -*-
# Кодировка UTF-8 для русского текста

import psycopg
import sys

# чтобы русский текст отображался
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg.connect(
    host='localhost',
    user='postgres',
    password='admin',
    dbname='project',
    autocommit=True
)

cursor = conn.cursor()

tables = [
    'roles',          # Роли пользователей
    'statuses',       # Статусы (заявок, офисов, договоров)
    'users',          # Пользователи системы
    'offices',        # Офисы для аренды
    'applications',   # Заявки на аренду
    'contracts',      # Договоры
    'payments',       # Платежи
    'office_views',   # Просмотры офисов
    'audit_log'       # Журнал действий
]

print('\n' + '='*60)
print('БАЗА ДАННЫХ project')
print('='*60 + '\n')

for table in tables:
    print('-'*60)
    print(f'TABLE: {table.upper()}')
    print('-'*60)
    
    # Получаем ВСЕ записи из таблицы (без LIMIT)
    cursor.execute(f'SELECT * FROM {table}')
    rows = cursor.fetchall()
    
    if rows:
        # Получаем названия колонок
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{table}' AND table_schema = 'public'
        """)
        cols = [c[0] for c in cursor.fetchall()]
        
        print(f'Columns: {", ".join(cols)}')  # Названия полей
        print(f'Total: {len(rows)} records\n')  # Количество записей
        
        for i, row in enumerate(rows, 1):
            print(f'{i}. {row}')
    else:
        print('Пусто') 
    
    print()


print('='*60)
print('Готово')
print('='*60 + '\n')

cursor.close() 
conn.close()  