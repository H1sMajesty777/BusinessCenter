#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИДЕАЛЬНЫЙ ГЕНЕРАТОР ДАННЫХ ДЛЯ ML МОДЕЛИ
Генерирует сбалансированные данные с правильными классами
"""

import psycopg
import random
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

def main():
    print('\n' + '='*60)
    print('🚀 ИДЕАЛЬНЫЙ ГЕНЕРАТОР ДАННЫХ ДЛЯ ML')
    print('='*60 + '\n')
    
    # Подключение
    conn = psycopg.connect(
        host='db',
        port=5432,
        user='postgres',
        password='admin',
        dbname='project'
    )
    cur = conn.cursor()
    
    # =========================================================
    # 1. ОЧИСТКА
    # =========================================================
    print('🗑️ Очистка старых данных...')
    cur.execute('TRUNCATE office_views, applications, contracts, payments RESTART IDENTITY CASCADE')
    conn.commit()
    print('✅ Очищено\n')
    
    # =========================================================
    # 2. ПОЛУЧАЕМ ОФИСЫ
    # =========================================================
    cur.execute('SELECT id, office_number, floor, price_per_month FROM offices')
    offices = cur.fetchall()
    print(f'📋 Офисов: {len(offices)}')
    
    # =========================================================
    # 3. СОЗДАЁМ КЛИЕНТОВ
    # =========================================================
    print('👥 Создание клиентов...')
    cur.execute("DELETE FROM users WHERE role_id = 3 AND login LIKE 'client_%'")
    
    for i in range(25):
        cur.execute("""
            INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
            VALUES (%s, crypt('client123', gen_salt('bf')), %s, %s, %s, 3, TRUE)
            ON CONFLICT (login) DO NOTHING
        """, (
            f'client_{i+1}',
            f'client{i+1}@example.com',
            f'+7 (999) 000-{i+1:02d}',
            f'Клиент {i+1}'
        ))
    conn.commit()
    
    cur.execute('SELECT id FROM users WHERE role_id = 3')
    users = [u[0] for u in cur.fetchall()]
    print(f'✅ Клиентов: {len(users)}\n')
    
    # =========================================================
    # 4. ГЕНЕРАЦИЯ ПРОСМОТРОВ
    # =========================================================
    print('📊 Генерация просмотров...')
    view_count = 0
    
    for office in offices:
        office_id = office[0]
        price = float(office[3])
        
        # Популярность офиса
        popularity = 1.0
        if price < 30000:
            popularity = 1.5
        elif price > 70000:
            popularity = 0.6
        
        for user_id in users[:15]:
            num_views = random.randint(5, 25)
            num_views = int(num_views * popularity)
            
            for _ in range(num_views):
                view_date = datetime.now() - timedelta(days=random.randint(1, 180))
                duration = random.randint(30, 600)
                is_contacted = random.random() < (0.2 + duration / 1000)
                
                cur.execute("""
                    INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, office_id, view_date, duration, is_contacted))
                view_count += 1
        
        if office_id % 5 == 0:
            print(f'   Обработано {office_id} офисов, создано {view_count} просмотров...')
    
    conn.commit()
    print(f'✅ Создано {view_count} просмотров\n')
    
    # =========================================================
    # 5. ГЕНЕРАЦИЯ ЗАЯВОК
    # =========================================================
    print('📝 Генерация заявок...')
    app_count = 0
    
    for office in offices:
        office_id = office[0]
        
        # Получаем кто смотрел этот офис
        cur.execute("""
            SELECT user_id, COUNT(*) as views, AVG(duration_seconds) as avg_duration
            FROM office_views
            WHERE office_id = %s AND user_id IS NOT NULL
            GROUP BY user_id
        """, (office_id,))
        viewers = cur.fetchall()
        
        for viewer in viewers:
            user_id, views, avg_duration = viewer
            
            # Конвертируем Decimal в float
            if isinstance(avg_duration, Decimal):
                avg_duration = float(avg_duration)
            elif avg_duration is None:
                avg_duration = 0
            
            views = int(views)
            
            # Вероятность подачи заявки
            prob = 0.1 + (views * 0.02) + (avg_duration / 600 * 0.1)
            prob = min(0.8, prob)
            
            if random.random() > prob:
                continue
            
            app_date = datetime.now() - timedelta(days=random.randint(1, 120))
            # Статус: 1-новая, 2-одобрена, 3-отказана
            status = random.choices([1, 2, 3], weights=[0.2, 0.6, 0.2])[0]
            
            comments = [
                'Хочу осмотреть офис',
                'Интересуют условия аренды',
                'Когда можно приехать?',
                'Есть ли скидки?',
                'Какие коммунальные платежи?'
            ]
            comment = random.choice(comments) if random.random() > 0.5 else None
            
            cur.execute("""
                INSERT INTO applications (user_id, office_id, status_id, comment, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, office_id, status, comment, app_date))
            app_count += 1
    
    conn.commit()
    print(f'✅ Создано {app_count} заявок\n')
    
    # =========================================================
    # 6. ГЕНЕРАЦИЯ ДОГОВОРОВ (ТОЛЬКО ДЛЯ ЧАСТИ ОФИСОВ)
    # =========================================================
    print('📄 Генерация договоров (только для 40% офисов)...')
    
    # Выбираем офисы для аренды (40% от всех)
    all_office_ids = [o[0] for o in offices]
    rented_offices = set(random.sample(all_office_ids, int(len(all_office_ids) * 0.4)))
    
    print(f'   Офисов с арендой: {len(rented_offices)}')
    print(f'   Офисов без аренды: {len(all_office_ids) - len(rented_offices)}')
    
    # Получаем одобренные заявки
    cur.execute("""
        SELECT a.id, a.user_id, a.office_id, a.created_at, o.price_per_month
        FROM applications a
        JOIN offices o ON a.office_id = o.id
        WHERE a.status_id = 2
        ORDER BY a.created_at
    """)
    approved_apps = cur.fetchall()
    
    contract_count = 0
    offices_with_contracts = set()
    
    for app in approved_apps:
        app_id, user_id, office_id, created_at, price = app
        price = float(price)
        
        # Создаём договор только если офис выбран для аренды
        if office_id not in rented_offices:
            continue
        
        if created_at.tzinfo:
            created_at = created_at.replace(tzinfo=None)
        
        # Дата подписания
        sign_date = created_at + timedelta(days=random.randint(1, 30))
        sign_date = min(sign_date, datetime.now())
        
        # Длительность
        months = random.choice([3, 6, 12, 24])
        end_date = sign_date + timedelta(days=months * 30)
        
        # Сумма со скидкой
        discount = random.uniform(0.85, 1.0)
        total = price * months * discount
        
        # Статус договора
        if end_date < datetime.now():
            status_id = 5  # истек
        else:
            status_id = 4  # действует
            offices_with_contracts.add(office_id)
            cur.execute('UPDATE offices SET is_free = FALSE WHERE id = %s', (office_id,))
        
        cur.execute("""
            INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (app_id, user_id, office_id, sign_date.date(), end_date.date(), total, status_id, sign_date))
        contract_count += 1
    
    conn.commit()
    print(f'✅ Создано {contract_count} договоров\n')
    
    # =========================================================
    # 7. ГЕНЕРАЦИЯ ПЛАТЕЖЕЙ
    # =========================================================
    print('💰 Генерация платежей...')
    
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
            
            # 80% платежей вовремя, 20% с задержкой
            if random.random() > 0.8:
                payment_date += timedelta(days=random.randint(1, 15))
                status_id = 9  # просрочено
            else:
                status_id = 8  # оплачено
            
            cur.execute("""
                INSERT INTO payments (contract_id, amount, payment_date, status_id, transaction_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                contract_id,
                Decimal(str(monthly * random.uniform(0.95, 1.05))),
                payment_date,
                status_id,
                f'TX_{random.randint(10000, 99999)}'
            ))
            payment_count += 1
    
    conn.commit()
    print(f'✅ Создано {payment_count} платежей\n')
    
    # =========================================================
    # 8. ПРОВЕРКА БАЛАНСА
    # =========================================================
    print('🔍 ПРОВЕРКА БАЛАНСА КЛАССОВ:')
    
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN c.id IS NOT NULL AND c.signed_at > NOW() - INTERVAL '6 months' THEN 1 END) as rented_recently,
            COUNT(CASE WHEN c.id IS NULL OR c.signed_at <= NOW() - INTERVAL '6 months' THEN 1 END) as not_rented_recently
        FROM offices o
        LEFT JOIN contracts c ON o.id = c.office_id
    """)
    balance = cur.fetchone()
    
    rented = balance[0] or 0
    not_rented = balance[1] or 0
    
    print(f'   📍 Арендованы недавно: {rented} офисов')
    print(f'   📍 Не арендованы: {not_rented} офисов')
    
    if rented > 0 and not_rented > 0:
        print('   ✅ ОТЛИЧНЫЙ БАЛАНС! Модель успешно обучится.')
    else:
        print('   ⚠️ ВНИМАНИЕ: Нет баланса классов!')
    
    # =========================================================
    # 9. ФИНАЛЬНАЯ СТАТИСТИКА
    # =========================================================
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM office_views) as views,
            (SELECT COUNT(*) FROM applications) as apps,
            (SELECT COUNT(*) FROM contracts) as contracts,
            (SELECT COUNT(*) FROM payments) as payments,
            (SELECT COUNT(*) FROM users WHERE role_id = 3) as clients
    """)
    stats = cur.fetchone()
    
    print('\n' + '='*60)
    print('📊 ФИНАЛЬНАЯ СТАТИСТИКА')
    print('='*60)
    print(f'   👁️ Просмотров: {stats[0]}')
    print(f'   📝 Заявок: {stats[1]}')
    print(f'   📄 Договоров: {stats[2]}')
    print(f'   💰 Платежей: {stats[3]}')
    print(f'   👥 Клиентов: {stats[4]}')
    
    if stats[1] > 0:
        conv_app = (stats[2] / stats[1]) * 100
        print(f'   📈 Конверсия заявка→договор: {conv_app:.1f}%')
    if stats[0] > 0:
        conv_view = (stats[1] / stats[0]) * 100
        print(f'   📈 Конверсия просмотр→заявка: {conv_view:.1f}%')
    
    # =========================================================
    # 10. ЗАВЕРШЕНИЕ
    # =========================================================
    cur.close()
    conn.close()
    
    print('\n' + '='*60)
    print('✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!')
    print('='*60)
    print('\n💡 Теперь выполни обучение модели через API:')
    print('   POST /api/ai/rental-prediction/train?force=true')
    print()

if __name__ == '__main__':
    main()