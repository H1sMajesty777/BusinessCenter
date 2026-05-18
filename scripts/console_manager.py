#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КОНСОЛЬНЫЙ МЕНЕДЖЕР ДЛЯ BUSINESS CENTER
Полное управление: генерация, очистка, ML модель
Запуск: python console_manager.py
"""

import psycopg
import subprocess
import sys
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Цвета
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_logo():
    logo = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   {Colors.BOLD}{Colors.WHITE}🏢 BUSINESS CENTER - КОНСОЛЬНЫЙ МЕНЕДЖЕР{Colors.RESET}{Colors.CYAN}                                  ║
║   {Colors.DIM}Полное управление: данные, офисы, ML модель, генерация{Colors.RESET}{Colors.CYAN}                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(logo)

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*62}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}{text.center(62)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*62}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.RESET}")

def get_db_connection():
    try:
        conn = psycopg.connect(
            host='db',
            port=5432,
            user='postgres',
            password='admin',
            dbname='project'
        )
        return conn
    except Exception as e:
        print_error(f"Ошибка подключения: {e}")
        return None

def get_stats():
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM offices")
    stats['total_offices'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM offices WHERE is_free = TRUE")
    stats['free_offices'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM offices WHERE is_free = FALSE")
    stats['rented_offices'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(id) FROM offices")
    stats['min_office_id'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT MAX(id) FROM offices")
    stats['max_office_id'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM office_views")
    stats['total_views'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM applications")
    stats['total_applications'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM contracts")
    stats['total_contracts'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM payments")
    stats['total_payments'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role_id = 3")
    stats['total_clients'] = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return stats

def print_stats(stats):
    print(f"{Colors.BOLD}📊 СТАТИСТИКА БАЗЫ ДАННЫХ{Colors.RESET}")
    print(f"{Colors.DIM}{'─'*40}{Colors.RESET}")
    print(f"   🏢 Всего офисов:        {stats['total_offices']}")
    print(f"   🟢 Свободных:           {stats['free_offices']}")
    print(f"   🔴 Арендованных:        {stats['rented_offices']}")
    print(f"   📏 Диапазон ID:         {stats['min_office_id']} - {stats['max_office_id']}")
    print(f"   👁️  Просмотров:          {stats['total_views']:,}")
    print(f"   📝 Заявок:              {stats['total_applications']:,}")
    print(f"   📄 Договоров:           {stats['total_contracts']:,}")
    print(f"   💰 Платежей:            {stats['total_payments']:,}")
    print(f"   👤 Клиентов:            {stats['total_clients']}")
    print()

def print_menu(title, items):
    print(f"\n{Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}")
    print(f"{Colors.DIM}{'─'*50}{Colors.RESET}")
    for key, (desc, color) in items.items():
        print(f"  {Colors.BOLD}{key}{Colors.RESET}. {color}{desc}{Colors.RESET}")
    print()

def input_number(prompt, min_val=None, max_val=None, default=None):
    """Ввод числа с валидацией"""
    while True:
        try:
            if default is not None:
                val = input(f"{prompt} [{default}]: ").strip()
                if not val:
                    return default
                val = int(val)
            else:
                val = int(input(f"{prompt}: ").strip())
            
            if min_val is not None and val < min_val:
                print_warning(f"Значение должно быть >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print_warning(f"Значение должно быть <= {max_val}")
                continue
            return val
        except ValueError:
            print_error("Введите число")

def input_yes_no(prompt, default='no'):
    """Ввод да/нет"""
    response = input(f"{prompt} (yes/no) [{default}]: ").strip().lower()
    if not response:
        return default == 'yes'
    return response == 'yes'

# =========================================================
# ГЕНЕРАТОРЫ
# =========================================================

def generate_clients():
    """Генерация клиентов"""
    print_header("ГЕНЕРАЦИЯ КЛИЕНТОВ")
    
    num_clients = input_number("Количество клиентов для генерации", min_val=1, max_val=200, default=50)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE role_id = 3 AND login LIKE 'client_%'")
        
        for i in range(num_clients):
            cursor.execute("""
                INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
                VALUES (%s, crypt('client123', gen_salt('bf')), %s, %s, %s, 3, TRUE)
                ON CONFLICT (login) DO NOTHING
            """, (
                f'client_{i+1}',
                f'client{i+1}@example.com',
                f'+7 (999) 000-{i+1:04d}',
                f'Клиент {i+1}'
            ))
        
        conn.commit()
        print_success(f"Создано {num_clients} клиентов")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def delete_clients():
    """Удаление сгенерированных клиентов"""
    print_header("УДАЛЕНИЕ КЛИЕНТОВ")
    
    if not input_yes_no("Удалить всех сгенерированных клиентов (client_*)?", default='no'):
        print_info("Операция отменена")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE role_id = 3 AND login LIKE 'client_%'")
        deleted = cursor.rowcount
        conn.commit()
        print_success(f"Удалено {deleted} клиентов")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_views():
    """Генерация просмотров с настройками"""
    print_header("ГЕНЕРАЦИЯ ПРОСМОТРОВ")
    
    days_back = input_number("За сколько дней генерировать историю", min_val=1, max_val=730, default=180)
    views_per_office = input_number("Максимум просмотров на офис", min_val=1, max_val=100, default=25)
    min_duration = input_number("Мин. длительность (сек)", min_val=5, max_val=60, default=30)
    max_duration = input_number("Макс. длительность (сек)", min_val=60, max_val=1200, default=600)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Получаем офисы
        cursor.execute('SELECT id, price_per_month FROM offices')
        offices = cursor.fetchall()
        
        # Получаем клиентов
        cursor.execute('SELECT id FROM users WHERE role_id = 3')
        users = [u[0] for u in cursor.fetchall()]
        
        if not users:
            print_error("Нет клиентов. Сначала сгенерируйте клиентов")
            return False
        
        print_info(f"Офисов: {len(offices)}, Клиентов: {len(users)}")
        
        view_count = 0
        
        for office in offices:
            office_id = office[0]
            price = float(office[1])
            
            # Популярность офиса от цены
            if price < 30000:
                popularity = 1.5
            elif price > 100000:
                popularity = 0.5
            else:
                popularity = 1.0
            
            for user_id in users[:30]:  # Используем первых 30 клиентов
                num_views = int(random.randint(5, views_per_office) * popularity)
                
                for _ in range(num_views):
                    days_ago = random.randint(1, days_back)
                    view_date = datetime.now() - timedelta(days=days_ago)
                    duration = random.randint(min_duration, max_duration)
                    is_contacted = random.random() < (0.15 + duration / 1000)
                    
                    cursor.execute("""
                        INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, office_id, view_date, duration, is_contacted))
                    view_count += 1
            
            if office_id % 10 == 0:
                print(f'   Обработано {office_id} офисов...')
        
        conn.commit()
        print_success(f"Создано {view_count} просмотров")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_applications():
    """Генерация заявок на основе просмотров"""
    print_header("ГЕНЕРАЦИЯ ЗАЯВОК")
    
    base_prob = input_number("Базовая вероятность заявки (%)", min_val=1, max_val=50, default=10) / 100
    days_back = input_number("За сколько дней генерировать заявки", min_val=1, max_val=365, default=120)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM offices')
        offices = cursor.fetchall()
        
        app_count = 0
        
        for office in offices:
            office_id = office[0]
            
            cursor.execute("""
                SELECT user_id, COUNT(*) as views, AVG(duration_seconds) as avg_duration
                FROM office_views
                WHERE office_id = %s AND user_id IS NOT NULL
                GROUP BY user_id
            """, (office_id,))
            viewers = cursor.fetchall()
            
            for viewer in viewers:
                user_id, views, avg_duration = viewer
                
                if isinstance(avg_duration, Decimal):
                    avg_duration = float(avg_duration)
                elif avg_duration is None:
                    avg_duration = 0
                
                prob = base_prob + (views * 0.02) + (avg_duration / 600 * 0.1)
                prob = min(0.8, prob)
                
                if random.random() > prob:
                    continue
                
                days_offset = random.randint(1, days_back)
                app_date = datetime.now() - timedelta(days=days_offset)
                status = random.choices([1, 2, 3], weights=[0.2, 0.6, 0.2])[0]
                
                comments = [
                    'Хочу осмотреть офис', 'Интересуют условия аренды',
                    'Когда можно приехать?', 'Есть ли скидки?',
                    'Какие коммунальные платежи?', 'Можно с животными?',
                    'Есть ли парковка?'
                ]
                comment = random.choice(comments) if random.random() > 0.5 else None
                
                cursor.execute("""
                    INSERT INTO applications (user_id, office_id, status_id, comment, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, office_id, status, comment, app_date))
                app_count += 1
        
        conn.commit()
        print_success(f"Создано {app_count} заявок")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_contracts():
    """Генерация договоров на основе заявок"""
    print_header("ГЕНЕРАЦИЯ ДОГОВОРОВ")
    
    rented_ratio = input_number("Процент арендованных офисов (%)", min_val=10, max_val=90, default=40) / 100
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM offices')
        all_office_ids = [o[0] for o in cursor.fetchall()]
        num_rented = int(len(all_office_ids) * rented_ratio)
        rented_offices = set(random.sample(all_office_ids, max(1, num_rented)))
        
        print_info(f"Офисов с арендой: {len(rented_offices)}")
        print_info(f"Офисов без аренды: {len(all_office_ids) - len(rented_offices)}")
        
        cursor.execute("""
            SELECT a.id, a.user_id, a.office_id, a.created_at, o.price_per_month
            FROM applications a
            JOIN offices o ON a.office_id = o.id
            WHERE a.status_id = 2
            ORDER BY a.created_at
        """)
        approved_apps = cursor.fetchall()
        
        contract_count = 0
        for app in approved_apps:
            app_id, user_id, office_id, created_at, price = app
            price = float(price)
            
            if office_id not in rented_offices:
                continue
            
            if created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)
            
            sign_date = created_at + timedelta(days=random.randint(1, 30))
            sign_date = min(sign_date, datetime.now())
            
            months = random.choices([3, 6, 12, 24, 36], weights=[0.1, 0.2, 0.4, 0.2, 0.1])[0]
            end_date = sign_date + timedelta(days=months * 30)
            
            discount = random.uniform(0.85, 1.0)
            total = price * months * discount
            
            if end_date < datetime.now():
                status_id = 5
            else:
                status_id = 4
                cursor.execute('UPDATE offices SET is_free = FALSE WHERE id = %s', (office_id,))
            
            cursor.execute("""
                INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (app_id, user_id, office_id, sign_date.date(), end_date.date(), total, status_id, sign_date))
            contract_count += 1
        
        conn.commit()
        print_success(f"Создано {contract_count} договоров")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_payments():
    """Генерация платежей на основе договоров"""
    print_header("ГЕНЕРАЦИЯ ПЛАТЕЖЕЙ")
    
    delay_prob = input_number("Вероятность задержки платежа (%)", min_val=0, max_val=50, default=20) / 100
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, start_date, end_date, total_amount FROM contracts')
        contracts = cursor.fetchall()
        
        if not contracts:
            print_warning("Нет договоров для генерации платежей")
            return False
        
        payment_count = 0
        for contract in contracts:
            contract_id, start_date, end_date, total_amount = contract
            total_amount = float(total_amount)
            
            months = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month))
            monthly = total_amount / months
            
            for m in range(months):
                payment_date = start_date + timedelta(days=m * 30)
                if payment_date > datetime.now().date():
                    continue
                
                if random.random() < delay_prob:
                    payment_date += timedelta(days=random.randint(1, 15))
                    status_id = 9
                else:
                    status_id = 8
                
                cursor.execute("""
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
        print_success(f"Создано {payment_count} платежей")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def run_full_generation():
    """Полная генерация всех данных"""
    print_header("ПОЛНАЯ ГЕНЕРАЦИЯ ДАННЫХ")
    
    if not input_yes_no("Запустить полную генерацию?", default='no'):
        print_info("Операция отменена")
        return False
    
    print_info("Очистка старых данных...")
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM payments")
        cursor.execute("DELETE FROM contracts")
        cursor.execute("DELETE FROM applications")
        cursor.execute("DELETE FROM office_views")
        cursor.execute("UPDATE offices SET is_free = TRUE")
        conn.commit()
        
        print_success("Очистка завершена")
        
        # Последовательная генерация
        if not generate_clients():
            return False
        
        if not generate_views():
            return False
        
        if not generate_applications():
            return False
        
        if not generate_contracts():
            return False
        
        if not generate_payments():
            return False
        
        print_success("\n🎉 ПОЛНАЯ ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def clean_all_data():
    """Полная очистка всех данных"""
    print_header("ОЧИСТКА ДАННЫХ")
    
    if not input_yes_no("Очистить все данные (просмотры, заявки, договоры, платежи)?", default='no'):
        print_info("Операция отменена")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM payments")
        cursor.execute("DELETE FROM contracts")
        cursor.execute("DELETE FROM applications")
        cursor.execute("DELETE FROM office_views")
        cursor.execute("UPDATE offices SET is_free = TRUE")
        conn.commit()
        
        print_success("Все данные очищены, статус офисов сброшен")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def delete_generated_offices():
    """Удалить сгенерированные офисы"""
    print_header("УДАЛЕНИЕ ОФИСОВ")
    
    if not input_yes_no("Удалить сгенерированные офисы (ID > 20)?", default='no'):
        print_info("Операция отменена")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM office_views WHERE office_id > 20")
        cursor.execute("DELETE FROM applications WHERE office_id > 20")
        cursor.execute("DELETE FROM contracts WHERE office_id > 20")
        cursor.execute("DELETE FROM offices WHERE id > 20")
        deleted = cursor.rowcount
        conn.commit()
        
        print_success(f"Удалено {deleted} сгенерированных офисов (оставлены ID 1-20)")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def run_ml_train():
    """Обучение ML модели"""
    print_header("ОБУЧЕНИЕ ML МОДЕЛИ")
    
    if not input_yes_no("Обучить ML модель на текущих данных?", default='no'):
        print_info("Операция отменена")
        return False
    
    try:
        import requests
        
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"login": "admin", "password": "admin123"}
        )
        
        if login_response.status_code != 200:
            print_error("Не удалось получить токен администратора")
            return False
        
        token = login_response.cookies.get('access_token')
        if not token:
            print_error("Токен не найден в Cookie")
            return False
        
        train_response = requests.post(
            "http://localhost:8000/api/ai/rental-prediction/train?force=true",
            cookies={"access_token": token}
        )
        
        if train_response.status_code == 200:
            print_success("ML модель успешно обучена")
            return True
        else:
            print_error(f"Ошибка обучения: {train_response.text}")
            return False
            
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False

def show_ml_metrics():
    """Показать метрики модели"""
    print_header("МЕТРИКИ ML МОДЕЛИ")
    
    try:
        import requests
        import json
        
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"login": "admin", "password": "admin123"}
        )
        
        if login_response.status_code != 200:
            print_error("Не удалось получить токен")
            return
        
        token = login_response.cookies.get('access_token')
        
        info_response = requests.get(
            "http://localhost:8000/api/ai/rental-prediction/model/info",
            cookies={"access_token": token}
        )
        
        if info_response.status_code == 200:
            data = info_response.json()
            print(f"   📊 Модель обучена: {data.get('is_trained', False)}")
            print(f"   🏷️ Версия: {data.get('metadata', {}).get('version', 'N/A')}")
            print(f"   📈 ROC AUC: {data.get('metadata', {}).get('metrics', {}).get('roc_auc', 'N/A')}")
            print(f"   🎯 Accuracy: {data.get('metadata', {}).get('metrics', {}).get('accuracy', 'N/A')}")
            print(f"   📊 F1 Score: {data.get('metadata', {}).get('metrics', {}).get('f1_score', 'N/A')}")
            print(f"   🔢 Количество признаков: {data.get('feature_count', 0)}")
        else:
            print_error("Не удалось получить информацию о модели")
            
    except Exception as e:
        print_error(f"Ошибка: {e}")

def main():
    while True:
        clear_screen()
        print_logo()
        
        stats = get_stats()
        if stats:
            print_stats(stats)
        
        print_menu("ГЛАВНОЕ МЕНЮ", {
            "1": ("🚀 ПОЛНАЯ ГЕНЕРАЦИЯ (все данные)", Colors.GREEN),
            "2": ("👥 ГЕНЕРАЦИЯ КЛИЕНТОВ", Colors.BLUE),
            "3": ("👁️ ГЕНЕРАЦИЯ ПРОСМОТРОВ", Colors.BLUE),
            "4": ("📝 ГЕНЕРАЦИЯ ЗАЯВОК", Colors.BLUE),
            "5": ("📄 ГЕНЕРАЦИЯ ДОГОВОРОВ", Colors.BLUE),
            "6": ("💰 ГЕНЕРАЦИЯ ПЛАТЕЖЕЙ", Colors.BLUE),
            "7": ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM),
            "8": ("🗑️ ОЧИСТИТЬ ВСЕ ДАННЫЕ", Colors.YELLOW),
            "9": ("🏢 УДАЛИТЬ СГЕНЕРИРОВАННЫЕ ОФИСЫ", Colors.RED),
            "10": ("👥 УДАЛИТЬ КЛИЕНТОВ", Colors.RED),
            "11": ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM),
            "12": ("🧠 ОБУЧИТЬ ML МОДЕЛЬ", Colors.PURPLE),
            "13": ("📊 ПОКАЗАТЬ МЕТРИКИ ML", Colors.PURPLE),
            "14": ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.DIM),
            "0": ("🚪 ВЫХОД", Colors.RED)
        })
        
        choice = input(f"{Colors.BOLD}Выберите действие: {Colors.RESET}").strip()
        
        if choice == "1":
            run_full_generation()
        elif choice == "2":
            generate_clients()
        elif choice == "3":
            generate_views()
        elif choice == "4":
            generate_applications()
        elif choice == "5":
            generate_contracts()
        elif choice == "6":
            generate_payments()
        elif choice == "8":
            clean_all_data()
        elif choice == "9":
            delete_generated_offices()
        elif choice == "10":
            delete_clients()
        elif choice == "12":
            run_ml_train()
        elif choice == "13":
            show_ml_metrics()
        elif choice == "0":
            print_success("До свидания!")
            sys.exit(0)
        
        if choice not in ["0"]:
            input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Прервано пользователем{Colors.RESET}")
        sys.exit(0)