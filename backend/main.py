# -*- coding: utf-8 -*-
import psycopg2
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    user='postgres',
    password='admin',
    dbname='project'
)
conn.set_client_encoding('UTF8')

cursor = conn.cursor()

tables = ['roles', 'statuses', 'users', 'offices', 'applications', 'contracts', 'payments', 'office_views', 'audit_log']

print('ТАБЛИЦЫ В БАЗЕ:')
for table in tables:
    cursor.execute(f'SELECT * FROM {table}')
    rows = cursor.fetchall()
    print(f'\n{table.upper()}: {len(rows)} записей')
    for row in rows[:5]:
        print(row)

conn.close()
print('\nГотово')