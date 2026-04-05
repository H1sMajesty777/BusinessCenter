# scripts/generate_realistic_data.py
#!/usr/bin/env python3
"""
Продвинутый генератор реалистичных данных для ML модели
Генерирует данные с правильными корреляциями и распределениями
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
import random
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

def main():
    print('\n' + '='*60)
    print('🚀 ПРОДВИНУТЫЙ ГЕНЕРАТОР РЕАЛИСТИЧНЫХ ДАННЫХ')
    print('='*60 + '\n')
    
    conn = psycopg.connect(
        host='db',
        port=5432,
        user='postgres',
        password='admin',
        dbname='project'
    )
    cur = conn.cursor()
    
    # 1. Очистка старых данных
    print('🗑️ Очистка старых данных...')
    cur.execute('TRUNCATE office_views, applications, contracts, payments RESTART IDENTITY CASCADE')
    conn.commit()
    print('✅ Очищено\n')
    
    # 2. Получаем офисы
    cur.execute('SELECT id, office_number, floor, area_sqm, price_per_month, is_free FROM offices')
    offices = cur.fetchall()
    print(f'📋 Офисов: {len(offices)}')
    
    # 3. Создаём/получаем клиентов
    cur.execute("SELECT id FROM users WHERE role_id = 3 AND login LIKE 'client_%'")
    users = [u[0] for u in cur.fetchall()]
    
    if len(users) < 30:
        print('👥 Создание новых клиентов...')
        for i in range(30 - len(users)):
            cur.execute("""
                INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
                VALUES (%s, crypt('client123', gen_salt('bf')), %s, %s, %s, 3, TRUE)
                ON CONFLICT (login) DO NOTHING
            """, (
                f'client_{len(users)+i+1}',
                f'client{len(users)+i+1}@example.com',
                f'+7 (999) 000-{len(users)+i+1:02d}',
                f'Клиент {len(users)+i+1}'
            ))
        conn.commit()
        cur.execute('SELECT id FROM users WHERE role_id = 3')
        users = [u[0] for u in cur.fetchall()]
    
    print(f'👥 Клиентов: {len(users)}\n')
    
    # 4. Параметры для реалистичной генерации
    np.random.seed(42)
    random.seed(42)
    
    # Базовые вероятности
    SEASONAL_FACTORS = {
        'winter': 0.7,  # Зимой меньше просмотров
        'spring': 1.2,  # Весной больше
        'summer': 1.1,  # Летом тоже активно
        'autumn': 1.0   # Осенью базово
    }
    
    # 5. Генерация просмотров (реалистичные паттерны)
    print('📊 Генерация просмотров с сезонными паттернами...')
    view_count = 0
    
    for office in offices:
        office_id = office[0]
        floor = office[2]
        area = float(office[3])
        price = float(office[4])
        is_free = office[5]
        
        # Базовое количество просмотров зависит от характеристик офиса
        base_views = 10
        if price < 30000:
            base_views += 15  # Дешёвые офисы популярнее
        elif price > 80000:
            base_views -= 5   # Дорогие - меньше
        if floor >= 4:
            base_views += 10   # Высокие этажи популярнее
        if area > 100:
            base_views += 5
        
        base_views = max(5, min(40, base_views))
        
        for user_id in users:
            # Не все клиенты смотрят все офисы
            if random.random() > 0.3:
                continue
            
            # Количество просмотров для этого пользователя
            num_views = np.random.poisson(base_views * 0.5)
            num_views = min(15, max(1, num_views))
            
            for _ in range(num_views):
                # Случайная дата с учетом сезонности
                days_ago = random.randint(1, 180)
                view_date = datetime.now() - timedelta(days=days_ago)
                
                # Сезонный фактор
                month = view_date.month
                if month in [12, 1, 2]:
                    season = 'winter'
                elif month in [3, 4, 5]:
                    season = 'spring'
                elif month in [6, 7, 8]:
                    season = 'summer'
                else:
                    season = 'autumn'
                
                # Пропускаем с вероятностью, обратной сезонности
                if random.random() > SEASONAL_FACTORS[season]:
                    continue
                
                # Длительность просмотра (чем дороже офис - тем дольше думают)
                duration = int(np.random.exponential(60) * (1 + price/100000))
                duration = min(900, max(10, duration))
                
                # Вероятность контакта зависит от длительности просмотра
                contact_prob = min(0.5, duration / 600)
                is_contacted = random.random() < contact_prob
                
                cur.execute("""
                    INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, office_id, view_date, duration, is_contacted))
                view_count += 1
        
        if office_id % 5 == 0:
            print(f'   Обработано {office_id} офисов, создано {view_count} просмотров...')
    
    conn.commit()
    print(f'✅ Создано {view_count} просмотров\n')
    
    # 6. Генерация заявок (на основе просмотров)
    print('📝 Генерация заявок...')
    app_count = 0
    
    for office in offices:
        office_id = office[0]
        price = float(office[4])
        
        # Получаем статистику просмотров для офиса
        cur.execute("""
            SELECT user_id, COUNT(*) as views, 
                   AVG(duration_seconds) as avg_duration,
                   SUM(CASE WHEN is_contacted THEN 1 ELSE 0 END) as contacts
            FROM office_views
            WHERE office_id = %s AND user_id IS NOT NULL
            GROUP BY user_id
        """, (office_id,))
        viewers = cur.fetchall()
        
        for viewer in viewers:
            user_id, views, avg_duration, contacts = viewer
            
            # Конвертируем Decimal
            avg_duration = float(avg_duration) if avg_duration else 0
            contacts = int(contacts) if contacts else 0
            
            # Вероятность заявки зависит от интереса
            interest_score = 0.1
            interest_score += min(0.3, views * 0.02)
            interest_score += min(0.2, avg_duration / 600)
            interest_score += min(0.2, contacts * 0.1)
            
            # Ценовой фактор
            if price < 30000:
                interest_score += 0.15
            elif price > 100000:
                interest_score -= 0.1
            
            interest_score = max(0.05, min(0.8, interest_score))
            
            if random.random() > interest_score:
                continue
            
            # Дата заявки (после просмотров)
            app_date = datetime.now() - timedelta(days=random.randint(1, 90))
            
            # Статус заявки (с реалистичными весами)
            # 1 - новая (20%), 2 - одобрена (60%), 3 - отклонена (20%)
            status = random.choices([1, 2, 3], weights=[0.2, 0.6, 0.2])[0]
            
            comments = [
                'Хочу осмотреть офис',
                'Интересуют условия аренды',
                'Когда можно приехать?',
                'Есть ли скидки?',
                'Какие коммунальные платежи?',
                'Можно ли срочно заключить договор?',
                'Есть ли парковка?'
            ]
            comment = random.choice(comments) if random.random() > 0.5 else None
            
            cur.execute("""
                INSERT INTO applications (user_id, office_id, status_id, comment, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, office_id, status, comment, app_date))
            app_count += 1
    
    conn.commit()
    print(f'✅ Создано {app_count} заявок\n')
    
    # 7. Генерация договоров (реалистичная конверсия)
    print('📄 Генерация договоров...')
    
    # Получаем одобренные заявки
    cur.execute("""
        SELECT a.id, a.user_id, a.office_id, a.created_at, o.price_per_month, o.floor
        FROM applications a
        JOIN offices o ON a.office_id = o.id
        WHERE a.status_id = 2
        ORDER BY a.created_at
    """)
    approved_apps = cur.fetchall()
    
    contract_count = 0
    offices_with_contracts = set()
    
    for app in approved_apps:
        app_id, user_id, office_id, created_at, price, floor = app
        price = float(price)
        
        # Конверсия заявки в договор (не все одобренные становятся договорами)
        conversion_prob = 0.7
        if price > 100000:
            conversion_prob -= 0.2
        if floor >= 4:
            conversion_prob += 0.1
        
        if random.random() > conversion_prob:
            continue
        
        if created_at.tzinfo:
            created_at = created_at.replace(tzinfo=None)
        
        # Дата подписания (через 1-14 дней после заявки)
        sign_date = created_at + timedelta(days=random.randint(1, 14))
        sign_date = min(sign_date, datetime.now())
        
        # Длительность договора (месяцы)
        months = random.choices([3, 6, 12, 24, 36], weights=[0.1, 0.2, 0.4, 0.2, 0.1])[0]
        end_date = sign_date + timedelta(days=months * 30)
        
        # Сумма со скидкой (5-20%)
        discount = random.uniform(0.8, 1.0)
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
    
    # 8. Генерация платежей
    print('💰 Генерация платежей...')
    
    cur.execute('SELECT id, start_date, end_date, total_amount FROM contracts')
    contracts = cur.fetchall()
    
    payment_count = 0
    for contract in contracts:
        contract_id, start_date, end_date, total_amount = contract
        total_amount = float(total_amount)
        
        # Количество месяцев
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months <= 0:
            months = 1
        
        monthly = total_amount / months
        
        for m in range(months):
            payment_date = start_date + timedelta(days=m * 30)
            if payment_date > datetime.now().date():
                continue
            
            # 70% платежей вовремя, 30% с задержкой
            if random.random() > 0.7:
                delay_days = random.randint(1, 30)
                payment_date += timedelta(days=delay_days)
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
    
    # 9. Финальная статистика
    print('🔍 ФИНАЛЬНАЯ СТАТИСТИКА:')
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM office_views) as views,
            (SELECT COUNT(*) FROM applications) as apps,
            (SELECT COUNT(*) FROM contracts) as contracts,
            (SELECT COUNT(*) FROM payments) as payments,
            (SELECT COUNT(*) FROM users WHERE role_id = 3) as clients,
            (SELECT COUNT(*) FROM offices WHERE is_free = FALSE) as rented_offices,
            (SELECT COUNT(*) FROM offices WHERE is_free = TRUE) as free_offices
    """)
    stats = cur.fetchone()
    
    print(f'   👁️ Просмотров: {stats[0]}')
    print(f'   📝 Заявок: {stats[1]}')
    print(f'   📄 Договоров: {stats[2]}')
    print(f'   💰 Платежей: {stats[3]}')
    print(f'   👥 Клиентов: {stats[4]}')
    print(f'   🏢 Арендовано офисов: {stats[5]}')
    print(f'   🏢 Свободно офисов: {stats[6]}')
    
    if stats[1] > 0:
        conv_app = (stats[2] / stats[1]) * 100
        print(f'   📈 Конверсия заявка→договор: {conv_app:.1f}%')
    if stats[0] > 0:
        conv_view = (stats[1] / stats[0]) * 100
        print(f'   📈 Конверсия просмотр→заявка: {conv_view:.1f}%')
    
    cur.close()
    conn.close()
    
    print('\n' + '='*60)
    print('✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!')
    print('='*60)
    print('\n💡 Теперь переобучите модель:')
    print('   docker exec -it business_center_api python /app/scripts/init_ml.py --force')
    print()

if __name__ == '__main__':
    main()