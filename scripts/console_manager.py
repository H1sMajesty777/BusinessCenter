# backend/scripts/console_manager.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Консольный менеджер для управления данными Business Center
Запуск: python console_manager.py
"""

import psycopg
import subprocess
import sys
import os
from datetime import datetime

# Цвета для красивого вывода
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
    """Очистка экрана"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_logo():
    """Печать логотипа"""
    logo = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                                  ║
║   {Colors.BOLD}{Colors.WHITE}🏢 BUSINESS CENTER - КОНСОЛЬНЫЙ МЕНЕДЖЕР{Colors.RESET}{Colors.CYAN}                    ║
║   {Colors.DIM}Управление данными офисов, заявок, договоров и ML модели{Colors.RESET}{Colors.CYAN}    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(logo)

def print_header(text):
    """Печать заголовка"""
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

def print_menu(title, items):
    """Печать меню"""
    print(f"\n{Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}")
    print(f"{Colors.DIM}{'─'*40}{Colors.RESET}")
    for key, (desc, color) in items.items():
        print(f"  {Colors.BOLD}{key}{Colors.RESET}. {color}{desc}{Colors.RESET}")
    print()

def get_db_connection():
    """Получение подключения к БД"""
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
    """Получить статистику базы данных"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    stats = {}
    
    # Офисы
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
    
    # Просмотры
    cursor.execute("SELECT COUNT(*) FROM office_views")
    stats['total_views'] = cursor.fetchone()[0]
    
    # Заявки
    cursor.execute("SELECT COUNT(*) FROM applications")
    stats['total_applications'] = cursor.fetchone()[0]
    
    # Договоры
    cursor.execute("SELECT COUNT(*) FROM contracts")
    stats['total_contracts'] = cursor.fetchone()[0]
    
    # Платежи
    cursor.execute("SELECT COUNT(*) FROM payments")
    stats['total_payments'] = cursor.fetchone()[0]
    
    # Клиенты
    cursor.execute("SELECT COUNT(*) FROM users WHERE role_id = 3")
    stats['total_clients'] = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return stats

def print_stats(stats):
    """Вывести статистику"""
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

def clear_all_data():
    """Очистить все данные (кроме офисов и пользователей)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # ВАЖНО: удаляем в правильном порядке (сначала дочерние таблицы)
        print_info("Удаление платежей...")
        cursor.execute("DELETE FROM payments")
        
        print_info("Удаление договоров...")
        cursor.execute("DELETE FROM contracts")
        
        print_info("Удаление заявок...")
        cursor.execute("DELETE FROM applications")
        
        print_info("Удаление просмотров...")
        cursor.execute("DELETE FROM office_views")
        
        conn.commit()
        print_success("Все данные (платежи, договоры, заявки, просмотры) очищены")
        return True
    except Exception as e:
        print_error(f"Ошибка очистки: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
        
def clear_offices():
    """Удалить все сгенерированные офисы (оставить начальные)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Узнаем, сколько офисов было в init.sql (обычно 20)
        cursor.execute("SELECT MIN(id) FROM offices")
        min_id = cursor.fetchone()[0] or 1
        keep_count = 20  # Оставляем первые 20 офисов из init.sql
        
        cursor.execute(f"DELETE FROM offices WHERE id > {keep_count}")
        deleted = cursor.rowcount
        conn.commit()
        
        print_success(f"Удалено {deleted} сгенерированных офисов (оставлены ID 1-{keep_count})")
        return True
    except Exception as e:
        print_error(f"Ошибка удаления: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def reset_offices_status():
    """Сбросить статус всех офисов на 'свободен'"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE offices SET is_free = TRUE")
        updated = cursor.rowcount
        conn.commit()
        print_success(f"Статус {updated} офисов сброшен на 'свободен'")
        return True
    except Exception as e:
        print_error(f"Ошибка сброса: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def run_generator():
    """Запустить генератор данных"""
    print_info("Запуск генератора данных...")
    result = subprocess.run(
        ["python", "/app/scripts/generate_advanced_data.py"],
        capture_output=False
    )
    return result.returncode == 0

def run_ml_train():
    """Обучить ML модель"""
    print_info("Запуск обучения ML модели...")
    
    # Получаем токен администратора
    import requests
    import json
    
    try:
        # Логинимся
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"login": "admin", "password": "admin123"}
        )
        
        if login_response.status_code != 200:
            print_error("Не удалось получить токен администратора")
            return False
        
        # Получаем токен из Cookie
        token = login_response.cookies.get('access_token')
        if not token:
            print_error("Токен не найден в Cookie")
            return False
        
        # Обучаем модель
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

def init_db():
    """Инициализировать базу данных из init.sql"""
    print_info("Инициализация базы данных...")
    
    result = subprocess.run(
        ["docker", "cp", "database/init.sql", "business_center_db:/tmp/init.sql"],
        capture_output=True
    )
    
    result = subprocess.run(
        ["docker", "exec", "-i", "business_center_db", "psql", "-U", "postgres", "-d", "project", "-f", "/tmp/init.sql"],
        capture_output=False
    )
    
    if result.returncode == 0:
        print_success("База данных инициализирована")
        return True
    else:
        print_error("Ошибка инициализации")
        return False

def main():
    while True:
        clear_screen()
        print_logo()
        
        # Показываем статистику
        stats = get_stats()
        if stats:
            print_stats(stats)
        else:
            print_error("Не удалось получить статистику")
        
        # Главное меню
        print_menu("ГЛАВНОЕ МЕНЮ", {
            "1": ("Генерация данных", Colors.GREEN),
            "2": ("Очистка данных", Colors.YELLOW),
            "3": ("Управление офисами", Colors.BLUE),
            "4": ("ML модель", Colors.PURPLE),
            "5": ("База данных", Colors.CYAN),
            "0": ("Выход", Colors.RED)
        })
        
        choice = input(f"{Colors.BOLD}Выберите действие (0-5): {Colors.RESET}").strip()
        
        if choice == "1":
            # Меню генерации
            while True:
                clear_screen()
                print_logo()
                print_header("ГЕНЕРАЦИЯ ДАННЫХ")
                
                print_menu("Что сгенерировать?", {
                    "1": ("Сгенерировать ВСЕ данные (просмотры, заявки, договоры)", Colors.GREEN),
                    "2": ("Сгенерировать только просмотры", Colors.BLUE),
                    "3": ("Сгенерировать только заявки", Colors.BLUE),
                    "4": ("Сгенерировать только договоры", Colors.BLUE),
                    "5": ("Сгенерировать + обучить ML модель", Colors.PURPLE),
                    "0": ("Назад", Colors.RED)
                })
                
                sub_choice = input(f"{Colors.BOLD}Выберите действие (0-5): {Colors.RESET}").strip()
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":
                    run_generator()
                    input("\nНажмите Enter для продолжения...")
                elif sub_choice == "5":
                    if run_generator():
                        run_ml_train()
                    input("\nНажмите Enter для продолжения...")
                else:
                    print_info("Функция в разработке")
                    input("\nНажмите Enter для продолжения...")
                    
        elif choice == "2":
            # Меню очистки
            while True:
                clear_screen()
                print_logo()
                print_header("ОЧИСТКА ДАННЫХ")
                
                print_menu("Что очистить?", {
                    "1": ("Очистить ВСЕ данные (просмотры, заявки, договоры)", Colors.YELLOW),
                    "2": ("Очистить только просмотры", Colors.BLUE),
                    "3": ("Очистить только заявки", Colors.BLUE),
                    "4": ("Очистить только договоры и платежи", Colors.BLUE),
                    "5": ("Очистить ВСЕ и сбросить статус офисов", Colors.RED),
                    "0": ("Назад", Colors.RED)
                })
                
                sub_choice = input(f"{Colors.BOLD}Выберите действие (0-5): {Colors.RESET}").strip()
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":
                    confirm = input(f"{Colors.RED}Удалить все данные? (yes/no): {Colors.RESET}")
                    if confirm.lower() == 'yes':
                        clear_all_data()
                    input("\nНажмите Enter для продолжения...")
                else:
                    print_info("Функция в разработке")
                    input("\nНажмите Enter для продолжения...")
                    
        elif choice == "3":
            # Меню управления офисами
            while True:
                clear_screen()
                print_logo()
                print_header("УПРАВЛЕНИЕ ОФИСАМИ")
                
                print_menu("Выберите действие:", {
                    "1": ("Удалить сгенерированные офисы (оставить начальные)", Colors.YELLOW),
                    "2": ("Сбросить статус всех офисов на 'свободен'", Colors.BLUE),
                    "3": ("Удалить ВСЕ офисы (полная очистка)", Colors.RED),
                    "4": ("Инициализировать начальные офисы из init.sql", Colors.GREEN),
                    "0": ("Назад", Colors.RED)
                })
                
                sub_choice = input(f"{Colors.BOLD}Выберите действие (0-4): {Colors.RESET}").strip()
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":
                    confirm = input(f"{Colors.YELLOW}Удалить сгенерированные офисы? (yes/no): {Colors.RESET}")
                    if confirm.lower() == 'yes':
                        clear_offices()
                    input("\nНажмите Enter для продолжения...")
                elif sub_choice == "2":
                    reset_offices_status()
                    input("\nНажмите Enter для продолжения...")
                elif sub_choice == "3":
                    confirm = input(f"{Colors.RED}Удалить ВСЕ офисы? (yes/no): {Colors.RESET}")
                    if confirm.lower() == 'yes':
                        conn = get_db_connection()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute("TRUNCATE offices RESTART IDENTITY CASCADE")
                            conn.commit()
                            cursor.close()
                            conn.close()
                            print_success("Все офисы удалены")
                    input("\nНажмите Enter для продолжения...")
                elif sub_choice == "4":
                    init_db()
                    input("\nНажмите Enter для продолжения...")
                    
        elif choice == "4":
            # Меню ML модели
            while True:
                clear_screen()
                print_logo()
                print_header("ML МОДЕЛЬ")
                
                print_menu("Выберите действие:", {
                    "1": ("Обучить ML модель", Colors.GREEN),
                    "2": ("Проверить статус модели", Colors.BLUE),
                    "3": ("Посмотреть важность признаков", Colors.PURPLE),
                    "0": ("Назад", Colors.RED)
                })
                
                sub_choice = input(f"{Colors.BOLD}Выберите действие (0-3): {Colors.RESET}").strip()
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":
                    run_ml_train()
                    input("\nНажмите Enter для продолжения...")
                else:
                    print_info("Функция в разработке")
                    input("\nНажмите Enter для продолжения...")
                    
        elif choice == "5":
            # Меню базы данных
            while True:
                clear_screen()
                print_logo()
                print_header("БАЗА ДАННЫХ")
                
                print_menu("Выберите действие:", {
                    "1": ("Показать список таблиц", Colors.BLUE),
                    "2": ("Показать топ офисов", Colors.BLUE),
                    "3": ("Открыть psql консоль", Colors.GREEN),
                    "0": ("Назад", Colors.RED)
                })
                
                sub_choice = input(f"{Colors.BOLD}Выберите действие (0-3): {Colors.RESET}").strip()
                
                if sub_choice == "0":
                    break
                elif sub_choice == "3":
                    print_info("Открываем psql. Введите \\q для выхода")
                    subprocess.run(["docker", "exec", "-it", "business_center_db", "psql", "-U", "postgres", "-d", "project"])
                else:
                    print_info("Функция в разработке")
                    input("\nНажмите Enter для продолжения...")
                    
        elif choice == "0":
            print_success("До свидания!")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Прервано пользователем{Colors.RESET}")
        sys.exit(0)