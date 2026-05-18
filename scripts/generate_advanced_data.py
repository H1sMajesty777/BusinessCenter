#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
РАСШИРЕННЫЙ ГЕНЕРАТОР ДАННЫХ ДЛЯ ML МОДЕЛИ
"""

import psycopg
import random
import json
from datetime import datetime, timedelta
from decimal import Decimal

# =========================================================
# КОНФИГУРАЦИЯ
# =========================================================
NUM_OFFICES_TO_ADD = 30
NUM_CLIENTS = 40
RENTED_RATIO = 0.45

def get_seasonal_factor(date):
    month = date.month
    if month in [3, 4, 5, 9, 10]:
        return 1.6
    elif month in [6, 7, 8]:
        return 0.5
    else:
        return 0.9

def get_duration_by_price(price):
    if price < 25000:
        return random.randint(10, 45)
    elif price < 60000:
        return random.randint(30, 120)
    elif price < 100000:
        return random.randint(60, 240)
    else:
        return random.randint(120, 600)

def main():
    print('\n' + '='*60)
    print('🚀 РАСШИРЕННЫЙ ГЕНЕРАТОР ДАННЫХ ДЛЯ ML')
    print('='*60 + '\n')
    
    conn = psycopg.connect(
        host='db',
        port=5432,
        user='postgres',
        password='admin',
        dbname='project'
    )
    cur = conn.cursor()
    
    # =========================================================
    # 1. ДОБАВЛЯЕМ НОВЫЕ ОФИСЫ
    # =========================================================
    print(f'📦 ДОБАВЛЕНИЕ {NUM_OFFICES_TO_ADD} НОВЫХ ОФИСОВ...')
    
    cur.execute('SELECT DISTINCT floor FROM offices ORDER BY floor')
    existing_floors = [f[0] for f in cur.fetchall()]
    if not existing_floors:
        existing_floors = list(range(1, 6))
    
    # Получаем существующие номера офисов
    cur.execute('SELECT office_number FROM offices')
    existing_offices = set([o[0] for o in cur.fetchall()])
    
    added = 0
    for i in range(NUM_OFFICES_TO_ADD * 2):
        if added >= NUM_OFFICES_TO_ADD:
            break
            
        floor = random.choice(existing_floors)
        num = random.randint(1, 99)
        office_number = f"{floor}{num:02d}"
        
        if office_number in existing_offices:
            continue
            
        existing_offices.add(office_number)
        
        area = random.choice([25, 35, 45, 55, 65, 80, 100, 120, 150, 180, 220])
        price_per_month = area * random.choice([400, 450, 500, 550, 600, 700, 800])
        price_per_month = round(price_per_month / 1000) * 1000
        
        description = f"Современный офис площадью {area} м² на {floor} этаже. " + random.choice([
            "Отличное освещение, панорамные окна.", "Ремонт класса А, кондиционирование.",
            "Удобная планировка, возможна перепланировка.", "Тихий этаж, вид на парк.",
            "Доступ 24/7, своя парковка.", "Премиальная отделка, готовая мебель."
        ])
        
        amenities = {
            "wifi": True,
            "parking": random.random() > 0.3,
            "kitchen": random.random() > 0.5,
            "conditioning": True,
            "elevator": floor > 3,
            "premium": area > 150 or price_per_month > 100000
        }
        
        cur.execute("""
            INSERT INTO offices (office_number, floor, area_sqm, price_per_month, description, amenities, is_free)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        """, (office_number, floor, area, price_per_month, description, json.dumps(amenities)))
        
        added += 1
        if added % 10 == 0:
            print(f'   Добавлено {added} / {NUM_OFFICES_TO_ADD} офисов...')
    
    conn.commit()
    print(f'✅ Добавлено {added} новых офисов')
    
    cur.execute('SELECT id, office_number, floor, price_per_month, area_sqm FROM offices')
    offices = cur.fetchall()
    print(f'✅ Всего офисов в системе: {len(offices)}\n')
    
    # =========================================================
    # 2. ОЧИСТКА СТАРЫХ ДАННЫХ (сначала удаляем зависимости)
    # =========================================================
    print('🗑️ ОЧИСТКА СТАРЫХ ДАННЫХ...')
    cur.execute('TRUNCATE payments RESTART IDENTITY CASCADE')
    cur.execute('TRUNCATE contracts RESTART IDENTITY CASCADE')
    cur.execute('TRUNCATE applications RESTART IDENTITY CASCADE')
    cur.execute('TRUNCATE office_views RESTART IDENTITY CASCADE')
    conn.commit()
    print('✅ Очищены все связанные данные\n')
    
    # =========================================================
    # 3. УДАЛЯЕМ СТАРЫХ КЛИЕНТОВ И СОЗДАЁМ НОВЫХ
    # =========================================================
    print(f'👥 УДАЛЕНИЕ СТАРЫХ КЛИЕНТОВ...')
    cur.execute("DELETE FROM users WHERE role_id = 3 AND login LIKE 'client_%'")
    conn.commit()
    
    print(f'👥 СОЗДАНИЕ {NUM_CLIENTS} НОВЫХ КЛИЕНТОВ...')
    for i in range(NUM_CLIENTS):
        try:
            cur.execute("""
                INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
                VALUES (%s, crypt('client123', gen_salt('bf')), %s, %s, %s, 3, TRUE)
            """, (
                f'client_{i+1}',
                f'client{i+1}@example.com',
                f'+7 (999) 000-{i+1:02d}',
                f'Клиент {i+1}'
            ))
        except Exception as e:
            print(f'   Предупреждение: {e}')
    conn.commit()
    
    cur.execute('SELECT id FROM users WHERE role_id = 3')
    users = [u[0] for u in cur.fetchall()]
    print(f'✅ Клиентов: {len(users)}\n')
    
    # =========================================================
    # 4. ГЕНЕРАЦИЯ ПРОСМОТРОВ
    # =========================================================
    print('👁️ ГЕНЕРАЦИЯ ПРОСМОТРОВ...')
    view_count = 0
    
    for office in offices:
        office_id = office[0]
        price = float(office[3])
        
        popularity = 1.0
        if price < 30000:
            popularity = 1.5
        elif price > 100000:
            popularity = 0.5
            
        for user_id in users[:30]:
            num_views = int(random.randint(3, 20) * popularity)
            
            for _ in range(num_views):
                days_ago = random.randint(1, 730)
                view_date = datetime.now() - timedelta(days=days_ago)
                
                seasonal_factor = get_seasonal_factor(view_date)
                if random.random() > seasonal_factor:
                    continue
                
                duration = get_duration_by_price(price)
                is_contacted = random.random() < (0.15 + duration / 800)
                
                cur.execute("""
                    INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, office_id, view_date, duration, is_contacted))
                view_count += 1
        
        if office_id % 10 == 0:
            print(f'   Обработано {office_id} офисов, создано {view_count} просмотров...')
    
    conn.commit()
    print(f'✅ Создано {view_count} просмотров\n')
    
    # =========================================================
    # 5. ГЕНЕРАЦИЯ ЗАЯВОК
    # =========================================================
    print('📝 ГЕНЕРАЦИЯ ЗАЯВОК...')
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
            elif avg_duration is None:
                avg_duration = 0
            
            prob = 0.1 + (views * 0.02) + (avg_duration / 600 * 0.15)
            prob = min(0.7, prob)
            
            if random.random() > prob:
                continue
            
            days_offset = random.randint(1, 90)
            app_date = datetime.now() - timedelta(days=days_offset)
            
            seasonal = get_seasonal_factor(app_date)
            if seasonal > 1:
                status = random.choices([1, 2, 3], weights=[0.15, 0.75, 0.10])[0]
            else:
                status = random.choices([1, 2, 3], weights=[0.25, 0.55, 0.20])[0]
            
            comments = [
                'Хочу осмотреть офис', 'Интересуют условия аренды',
                'Когда можно приехать?', 'Есть ли скидки?'
            ]
            comment = random.choice(comments) if random.random() > 0.4 else None
            
            cur.execute("""
                INSERT INTO applications (user_id, office_id, status_id, comment, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, office_id, status, comment, app_date))
            app_count += 1
    
    conn.commit()
    print(f'✅ Создано {app_count} заявок\n')
    
    # =========================================================
    # 6. ГЕНЕРАЦИЯ ДОГОВОРОВ
    # =========================================================
    print('📄 ГЕНЕРАЦИЯ ДОГОВОРОВ...')
    
    all_office_ids = [o[0] for o in offices]
    num_rented = int(len(all_office_ids) * RENTED_RATIO)
    rented_offices = set(random.sample(all_office_ids, max(1, num_rented)))
    
    print(f'   Офисов с арендой: {len(rented_offices)}')
    print(f'   Офисов без аренды: {len(all_office_ids) - len(rented_offices)}')
    
    cur.execute("""
        SELECT a.id, a.user_id, a.office_id, a.created_at, o.price_per_month
        FROM applications a
        JOIN offices o ON a.office_id = o.id
        WHERE a.status_id = 2
        ORDER BY a.created_at
    """)
    approved_apps = cur.fetchall()
    
    contract_count = 0
    for app in approved_apps:
        app_id, user_id, office_id, created_at, price = app
        price = float(price)
        
        if office_id not in rented_offices:
            continue
        
        if created_at.tzinfo:
            created_at = created_at.replace(tzinfo=None)
        
        sign_date = created_at + timedelta(days=random.randint(1, 20))
        sign_date = min(sign_date, datetime.now())
        
        months = random.choices([3, 6, 12, 24], weights=[0.1, 0.2, 0.5, 0.2])[0]
        end_date = sign_date + timedelta(days=months * 30)
        
        total = price * months * random.uniform(0.85, 1.0)
        
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
    print(f'✅ Создано {contract_count} договоров\n')
    
    # =========================================================
    # 7. ФИНАЛЬНАЯ СТАТИСТИКА
    # =========================================================
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM office_views) as views,
            (SELECT COUNT(*) FROM applications) as apps,
            (SELECT COUNT(*) FROM contracts) as contracts,
            (SELECT COUNT(*) FROM users WHERE role_id = 3) as clients,
            (SELECT COUNT(*) FROM offices) as offices
    """)
    stats = cur.fetchone()
    
    print('='*60)
    print('📊 ФИНАЛЬНАЯ СТАТИСТИКА')
    print('='*60)
    print(f'   📍 Офисов: {stats[4]}')
    print(f'   👥 Клиентов: {stats[3]}')
    print(f'   👁️ Просмотров: {stats[0]}')
    print(f'   📝 Заявок: {stats[1]}')
    print(f'   📄 Договоров: {stats[2]}')
    
    if stats[1] > 0:
        conv = (stats[2] / stats[1]) * 100
        print(f'   📈 Конверсия заявка→договор: {conv:.1f}%')
    
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN c.id IS NOT NULL AND c.signed_at > NOW() - INTERVAL '6 months' THEN 1 END) as rented,
            COUNT(CASE WHEN c.id IS NULL OR c.signed_at <= NOW() - INTERVAL '6 months' THEN 1 END) as not_rented
        FROM offices o
        LEFT JOIN contracts c ON o.id = c.office_id
    """)
    balance = cur.fetchone()
    
    print(f'\n   🎯 АРЕНДОВАНЫ (целевой класс): {balance[0] or 0} офисов')
    print(f'   🎯 НЕ АРЕНДОВАНЫ: {balance[1] or 0} офисов')
    
    if balance[0] > 0 and balance[1] > 0:
        print('\n   ✅ ОТЛИЧНЫЙ БАЛАНС! Модель успешно обучится.')
    else:
        print('\n   ⚠️ ВНИМАНИЕ: Нет баланса классов! Добавьте больше данных.')
    
    cur.close()
    conn.close()
    
    print('\n' + '='*60)
    print('🎉 ГЕНЕРАЦИЯ ЗАВЕРШЕНА!')
    print('='*60)

if __name__ == '__main__':
    main()