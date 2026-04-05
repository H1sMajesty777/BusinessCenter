# -*- coding: utf-8 -*-
"""
Скрипт для генерации синтетических данных для обучения ML модели
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from psycopg.rows import dict_row

# Конфигурация подключения (правильная для Docker)
DB_CONFIG = {
    'host': 'db',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'project',
    'connect_timeout': 10
}

def get_offices(conn):
    """Получение списка офисов"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, office_number, floor, area_sqm, price_per_month FROM offices")
    offices = cursor.fetchall()
    cursor.close()
    return offices

def get_users(conn):
    """Получение списка пользователей (только клиенты)"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role_id = 3")
    users = cursor.fetchall()
    cursor.close()
    return users

def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("ГЕНЕРАЦИЯ СИНТЕТИЧЕСКИХ ДАННЫХ ДЛЯ ML МОДЕЛИ")
    print("="*60 + "\n")
    
    try:
        # Подключение к БД
        print("Подключение к PostgreSQL...")
        conn = psycopg.connect(**DB_CONFIG)
        conn.row_factory = dict_row
        print("Подключение к БД установлено\n")
        
        # Получаем данные
        offices = get_offices(conn)
        users = get_users(conn)
        
        print(f"Найдено офисов: {len(offices)}")
        print(f"Найдено пользователей-клиентов: {len(users)}")
        print()
        
        if len(offices) == 0:
            print("Нет офисов в базе! Сначала выполни full_bd.sql")
            return
        
        # Генерируем просмотры
        print("Генерация просмотров офисов...")
        cursor = conn.cursor()
        view_count = 0
        
        for office in offices:
            # Количество просмотров для офиса (5-50)
            num_views = random.randint(5, 50)
            
            for _ in range(num_views):
                user_id = random.choice(users)['id'] if users and random.random() > 0.3 else None
                view_date = datetime.now() - timedelta(days=random.randint(1, 90))
                duration = random.randint(10, 300)
                is_contacted = random.random() < 0.3
                
                try:
                    cursor.execute("""
                        INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, office['id'], view_date, duration, is_contacted))
                    view_count += 1
                except Exception as e:
                    pass
            
            if office['id'] % 5 == 0:
                print(f"   Обработано {office['id']} офисов...")
        
        conn.commit()
        print(f"Создано {view_count} просмотров")
        
        # Генерируем заявки
        print("Генерация заявок...")
        app_count = 0
        
        for office in offices:
            # Получаем количество просмотров для офиса
            cursor.execute("SELECT COUNT(*) as cnt FROM office_views WHERE office_id = %s", (office['id'],))
            views = cursor.fetchone()['cnt']
            
            if views == 0:
                continue
            
            # Количество заявок (5-20% от просмотров)
            num_apps = random.randint(1, max(1, int(views * 0.2)))
            num_apps = min(num_apps, 20)
            
            for _ in range(num_apps):
                user_id = random.choice(users)['id'] if users else None
                app_date = datetime.now() - timedelta(days=random.randint(1, 60))
                # Статус: 1=новая, 2=одобрена, 3=отказана
                status_id = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]
                
                comments = [
                    "Хочу посмотреть офис", 
                    "Интересуют условия аренды",
                    "Когда можно приехать на просмотр?",
                    "Есть ли возможность срочной аренды?"
                ]
                comment = random.choice(comments) if random.random() > 0.5 else None
                
                try:
                    cursor.execute("""
                        INSERT INTO applications (user_id, office_id, status_id, comment, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, office['id'], status_id, comment, app_date))
                    app_count += 1
                except Exception as e:
                    pass
        
        conn.commit()
        print(f"Создано {app_count} заявок")
        
        print("\n" + "="*60)
        print("ГЕНЕРАЦИЯ ДАННЫХ ЗАВЕРШЕНА!")
        print("="*60)
        
        # Показываем статистику
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM office_views) as views,
                (SELECT COUNT(*) FROM applications) as apps,
                (SELECT COUNT(*) FROM users WHERE role_id = 3) as clients
        """)
        stats = cursor.fetchone()
        
        print(f"\nИтоговая статистика:")
        print(f"   Всего просмотров: {stats['views']}")
        print(f"   Всего заявок: {stats['apps']}")
        print(f"   Всего клиентов: {stats['clients']}")
        
        cursor.close()
        conn.close()
        
        print("\n💡 Теперь можно обучить ML модель через API:")
        print("   POST /api/ai/rental-prediction/train")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()