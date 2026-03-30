#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg
import random
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

print('Генерация продвинутых данных...')

conn = psycopg.connect(host='db', user='postgres', password='admin', dbname='project')
cur = conn.cursor()

# 1. Получаем офисы
cur.execute('SELECT id, floor, price_per_month FROM offices')
offices = cur.fetchall()
print(f'Офисов: {len(offices)}')

# 2. Получаем/создаём пользователей
cur.execute("SELECT id FROM users WHERE role_id = 3")
users = [u[0] for u in cur.fetchall()]

if len(users) < 5:
    for i in range(5):
        cur.execute("""
            INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
            VALUES (%s, crypt('123', gen_salt('bf')), %s, %s, %s, 3, TRUE)
            ON CONFLICT (login) DO NOTHING
        """, (f'client_{i+1}', f'client{i+1}@test.com', f'+7(999)000-00-0{i+1}', f'Клиент {i+1}'))
    conn.commit()
    cur.execute('SELECT id FROM users WHERE role_id = 3')
    users = [u[0] for u in cur.fetchall()]

print(f'Клиентов: {len(users)}')

# 3. Очищаем старые данные
cur.execute('TRUNCATE office_views, applications, contracts, payments RESTART IDENTITY CASCADE')
conn.commit()

# 4. Генерируем просмотры
print(' Генерация просмотров...')
view_count = 0
for office in offices[:20]:
    office_id, floor, price = office
    price = float(price)
    
    for user_id in users[:10]:
        popularity = 1.0
        if floor >= 4:
            popularity *= 1.5
        if price < 30000:
            popularity *= 1.5
        elif price > 70000:
            popularity *= 0.7
        
        num_views = int(np.random.poisson(3 * popularity))
        num_views = min(15, num_views)
        
        for _ in range(num_views):
            view_date = datetime.now() - timedelta(days=random.randint(1, 180))
            duration = random.randint(10, 600)
            is_contacted = random.random() < 0.3
            
            cur.execute("""
                INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, office_id, view_date, duration, is_contacted))
            view_count += 1

conn.commit()
print(f'Создано {view_count} просмотров')

# 5. Генерируем заявки
print('Генерация заявок...')
app_count = 0

for office in offices[:20]:
    office_id = office[0]
    
    cur.execute("""
        SELECT user_id, COUNT(*) as views, AVG(duration_seconds) as avg_duration
        FROM office_views
        WHERE office_id = %s AND user_id IS NOT NULL
        GROUP BY user_id
    """, (office_id,))
    viewers = cur.fetchall()
    
    for viewer in viewers:
        user_id, views, avg_duration = viewer
        avg_duration = avg_duration or 0
        
        prob = 0.05 + (views * 0.02) + (avg_duration / 600 * 0.1)
        prob = min(0.8, prob)
        
        if random.random() > prob:
            continue
        
        app_date = datetime.now() - timedelta(days=random.randint(1, 90))
        status = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]
        
        cur.execute("""
            INSERT INTO applications (user_id, office_id, status_id, comment, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, office_id, status, 'Тестовая заявка', app_date))
        app_count += 1

conn.commit()
print(f'Создано {app_count} заявок')

# 6. Генерируем договоры
print('Генерация договоров...')

cur.execute("""
    SELECT a.id, a.user_id, a.office_id, a.created_at, o.price_per_month
    FROM applications a
    JOIN offices o ON a.office_id = o.id
    WHERE a.status_id = 2
    LIMIT 100
""")
approved = cur.fetchall()

contract_count = 0
for app in approved:
    app_id, user_id, office_id, created_at, price = app
    price = float(price)
    
    if created_at.tzinfo:
        created_at = created_at.replace(tzinfo=None)
    
    sign_date = created_at + timedelta(days=random.randint(1, 21))
    sign_date = min(sign_date, datetime.now())
    
    months = random.choice([3, 6, 12])
    end_date = sign_date + timedelta(days=months * 30)
    
    discount = random.uniform(0.85, 1.0)
    total = price * months * discount
    
    if end_date < datetime.now():
        status_id = 5
    else:
        status_id = 4
        cur.execute('UPDATE offices SET is_free = FALSE WHERE id = %s', (office_id,))
    
    cur.execute("""
        INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (app_id, user_id, office_id, sign_date.date(), end_date.date(), total, status_id, sign_date))
    contract_count += 1

conn.commit()
print(f'✅ Создано {contract_count} договоров')

# 7. Генерируем платежи
print('Генерация платежей...')

cur.execute('SELECT id, start_date, end_date, total_amount FROM contracts')
contracts = cur.fetchall()

payment_count = 0
for contract in contracts:
    contract_id, start_date, end_date, total_amount = contract
    total_amount = float(total_amount)
    
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if months <= 0:
        months = 1
    
    monthly = total_amount / months
    
    for m in range(months):
        payment_date = start_date + timedelta(days=m * 30)
        if payment_date > datetime.now().date():
            continue
        
        cur.execute("""
            INSERT INTO payments (contract_id, amount, payment_date, status_id, transaction_id)
            VALUES (%s, %s, %s, 8, %s)
        """, (contract_id, Decimal(str(monthly * random.uniform(0.95, 1.05))), payment_date, f'TX_{random.randint(10000,99999)}'))
        payment_count += 1

conn.commit()
print(f'Создано {payment_count} платежей')

# Статистика
cur.execute("""
    SELECT 
        (SELECT COUNT(*) FROM office_views) as views,
        (SELECT COUNT(*) FROM applications) as apps,
        (SELECT COUNT(*) FROM contracts) as contracts,
        (SELECT COUNT(*) FROM payments) as payments
""")
stats = cur.fetchone()

print('\n' + '='*60)
print('ФИНАЛЬНАЯ СТАТИСТИКА')
print('='*60)
print(f'   Просмотров: {stats[0]}')
print(f'   Заявок: {stats[1]}')
print(f'   Договоров: {stats[2]}')
print(f'   Платежей: {stats[3]}')
print(f'   Клиентов: {len(users)}')

cur.close()
conn.close()
print('\nГотово!')