#!/usr/bin/env python3
import psycopg
import random
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

conn = psycopg.connect(host='db', user='postgres', password='admin', dbname='project')
cur = conn.cursor()

print('🚀 ГЕНЕРАЦИЯ СБАЛАНСИРОВАННЫХ ДАННЫХ')
print('='*60)

# Очищаем всё
cur.execute('TRUNCATE office_views, applications, contracts, payments RESTART IDENTITY CASCADE')
conn.commit()

# Получаем офисы
cur.execute('SELECT id, office_number, floor, price_per_month FROM offices')
offices = cur.fetchall()
print(f'Офисов: {len(offices)}')

# Создаём клиентов
cur.execute("DELETE FROM users WHERE role_id = 3 AND login LIKE 'client_%'")
for i in range(30):
    cur.execute("""
        INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
        VALUES (%s, crypt('123', gen_salt('bf')), %s, %s, %s, 3, TRUE)
        ON CONFLICT (login) DO NOTHING
    """, (f'client_{i+1}', f'client{i+1}@test.com', f'+7(999)000-00-{i+1:02d}', f'Клиент {i+1}'))
conn.commit()

cur.execute('SELECT id FROM users WHERE role_id = 3')
users = [u[0] for u in cur.fetchall()]
print(f'Клиентов: {len(users)}')

# 1. Просмотры
print('\n📊 Генерация просмотров...')
view_count = 0
for office in offices:
    office_id = office[0]
    for user_id in users[:20]:
        views_per_user = random.randint(3, 25)
        for _ in range(views_per_user):
            view_date = datetime.now() - timedelta(days=random.randint(1, 180))
            duration = random.randint(30, 600)
            is_contacted = random.random() < 0.3
            cur.execute("""
                INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, office_id, view_date, duration, is_contacted))
            view_count += 1
conn.commit()
print(f'✅ Создано {view_count} просмотров')

# 2. Заявки
print('\n📝 Генерация заявок...')
app_count = 0
for office in offices:
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
        if isinstance(avg_duration, Decimal):
            avg_duration = float(avg_duration)
        prob = 0.1 + (views * 0.03) + (avg_duration / 600 * 0.15)
        prob = min(0.8, prob)
        if random.random() > prob:
            continue
        app_date = datetime.now() - timedelta(days=random.randint(1, 120))
        status = random.choices([1, 2, 3], weights=[0.2, 0.6, 0.2])[0]
        cur.execute("""
            INSERT INTO applications (user_id, office_id, status_id, comment, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, office_id, status, 'Заявка на аренду', app_date))
        app_count += 1
conn.commit()
print(f'✅ Создано {app_count} заявок')

# 3. Договоры
print('\n📄 Генерация договоров...')
cur.execute("""
    SELECT a.id, a.user_id, a.office_id, a.created_at, o.price_per_month
    FROM applications a
    JOIN offices o ON a.office_id = o.id
    WHERE a.status_id = 2
""")
approved = cur.fetchall()

offices_with_contracts = set()
contract_count = 0
for app in approved:
    app_id, user_id, office_id, created_at, price = app
    price = float(price)
    if created_at.tzinfo:
        created_at = created_at.replace(tzinfo=None)
    
    if random.random() < 0.6:
        sign_date = created_at + timedelta(days=random.randint(1, 21))
        sign_date = min(sign_date, datetime.now())
        months = random.choice([6, 12])
        end_date = sign_date + timedelta(days=months * 30)
        total = price * months * random.uniform(0.85, 1.0)
        if end_date < datetime.now():
            status_id = 5
        else:
            status_id = 4
            offices_with_contracts.add(office_id)
            cur.execute('UPDATE offices SET is_free = FALSE WHERE id = %s', (office_id,))
        cur.execute("""
            INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (app_id, user_id, office_id, sign_date.date(), end_date.date(), total, status_id, sign_date))
        contract_count += 1
conn.commit()
print(f'✅ Создано {contract_count} договоров')
print(f'   Офисов с договорами: {len(offices_with_contracts)}')

# 4. Платежи
print('\n💰 Генерация платежей...')
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
print(f'✅ Создано {payment_count} платежей')

# 5. Проверка баланса
print('\n🔍 ПРОВЕРКА ЦЕЛЕВОЙ ПЕРЕМЕННОЙ:')
cur.execute("""
    SELECT 
        COUNT(CASE WHEN c.id IS NOT NULL AND c.signed_at > NOW() - INTERVAL '6 months' THEN 1 END) as rented,
        COUNT(CASE WHEN c.id IS NULL OR c.signed_at <= NOW() - INTERVAL '6 months' THEN 1 END) as not_rented
    FROM offices o
    LEFT JOIN contracts c ON o.id = c.office_id
""")
balance = cur.fetchone()
print(f'   Арендованы недавно: {balance[0]} офисов')
print(f'   Не арендованы: {balance[1]} офисов')

if balance[0] > 0 and balance[1] > 0:
    print('   ✅ БАЛАНС ЕСТЬ! Можно обучать.')
else:
    print('   ❌ НЕТ БАЛАНСА!')

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
print('📊 ФИНАЛЬНАЯ СТАТИСТИКА')
print('='*60)
print(f'   Просмотров: {stats[0]}')
print(f'   Заявок: {stats[1]}')
print(f'   Договоров: {stats[2]}')
print(f'   Платежей: {stats[3]}')

cur.close()
conn.close()
print('\n✅ Готово!')