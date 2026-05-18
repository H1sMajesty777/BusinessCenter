#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки данных по офисам (ПРАВИЛЬНЫЙ ПОРЯДОК)
Запуск: python clean_offices_data_fixed.py
"""

import psycopg
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.RESET}")

def main():
    print('\n' + '='*60)
    print('🗑️ ОЧИСТКА ГЕНЕРИРОВАННЫХ ДАННЫХ')
    print('='*60 + '\n')
    
    conn = psycopg.connect(
        host='db',
        port=5432,
        user='postgres',
        password='admin',
        dbname='project'
    )
    cur = conn.cursor()
    print_success("Подключение к базе данных установлено")
    
    # Показываем текущую статистику
    print_info("Текущая статистика перед очисткой:")
    cur.execute("SELECT COUNT(*) FROM office_views")
    views = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications")
    apps = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM contracts")
    contracts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM payments")
    payments = cur.fetchone()[0]
    
    print(f"   👁️ Просмотров: {views}")
    print(f"   📝 Заявок: {apps}")
    print(f"   📄 Договоров: {contracts}")
    print(f"   💰 Платежей: {payments}")
    
    # Правильный порядок очистки (от зависимых к независимым)
    print_info("\nОчистка данных в правильном порядке...")
    
    try:
        # 1. Сначала платежи (зависят от договоров)
        cur.execute("TRUNCATE payments CASCADE")
        conn.commit()
        print_success("Платежи очищены")
        
        # 2. Договоры (зависят от заявок и офисов)
        cur.execute("TRUNCATE contracts CASCADE")
        conn.commit()
        print_success("Договоры очищены")
        
        # 3. Заявки (зависят от офисов и пользователей)
        cur.execute("TRUNCATE applications CASCADE")
        conn.commit()
        print_success("Заявки очищены")
        
        # 4. Просмотры (зависят от офисов и пользователей)
        cur.execute("TRUNCATE office_views CASCADE")
        conn.commit()
        print_success("Просмотры очищены")
        
        # 5. Сбрасываем статус офисов на "свободен"
        cur.execute("UPDATE offices SET is_free = TRUE")
        conn.commit()
        print_success("Статус всех офисов сброшен на 'свободен'")
        
        # Показываем новую статистику
        print_info("\nСтатистика после очистки:")
        cur.execute("SELECT COUNT(*) FROM office_views")
        print(f"   👁️ Просмотров: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM applications")
        print(f"   📝 Заявок: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM contracts")
        print(f"   📄 Договоров: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM payments")
        print(f"   💰 Платежей: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM offices WHERE is_free = TRUE")
        free = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM offices")
        total = cur.fetchone()[0]
        print(f"   🏢 Свободных офисов: {free} / {total}")
        
        print("\n" + '='*60)
        print_success("ОЧИСТКА ЗАВЕРШЕНА УСПЕШНО!")
        print('='*60)
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        print_info("Соединение с базой данных закрыто")

if __name__ == "__main__":
    main()