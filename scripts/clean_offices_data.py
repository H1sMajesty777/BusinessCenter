# backend/scripts/clean_offices_data.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки данных по офисам
Запуск: python clean_offices_data.py [--all] [--views] [--applications] [--contracts] [--offices] [--force]
"""

import psycopg
import sys
import argparse
from datetime import datetime

# Цвета для вывода
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

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.RESET}")

def get_stats(cursor):
    """Получить статистику перед очисткой"""
    stats = {}
    
    # Офисы
    cursor.execute("SELECT COUNT(*) FROM offices")
    stats['total_offices'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM offices WHERE is_free = TRUE")
    stats['free_offices'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM offices WHERE is_free = FALSE")
    stats['rented_offices'] = cursor.fetchone()[0]
    
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
    
    return stats

def print_stats(stats):
    """Вывести статистику"""
    print(f"{Colors.BOLD}📊 ТЕКУЩАЯ СТАТИСТИКА:{Colors.RESET}")
    print(f"   🏢 Офисов всего: {stats['total_offices']}")
    print(f"   🟢 Свободных офисов: {stats['free_offices']}")
    print(f"   🔴 Арендованных офисов: {stats['rented_offices']}")
    print(f"   👁️ Просмотров: {stats['total_views']}")
    print(f"   📝 Заявок: {stats['total_applications']}")
    print(f"   📄 Договоров: {stats['total_contracts']}")
    print(f"   💰 Платежей: {stats['total_payments']}")

def clean_office_views(cursor, conn, dry_run=False):
    """Очистить просмотры офисов"""
    if dry_run:
        cursor.execute("SELECT COUNT(*) FROM office_views")
        count = cursor.fetchone()[0]
        print_info(f"Будет удалено {count} записей просмотров")
        return count
    
    cursor.execute("DELETE FROM office_views")
    conn.commit()
    print_success("Просмотры офисов очищены")
    return 0

def clean_applications(cursor, conn, dry_run=False):
    """Очистить заявки"""
    if dry_run:
        cursor.execute("SELECT COUNT(*) FROM applications")
        count = cursor.fetchone()[0]
        print_info(f"Будет удалено {count} заявок")
        return count
    
    cursor.execute("DELETE FROM applications")
    conn.commit()
    print_success("Заявки очищены")
    return 0

def clean_contracts(cursor, conn, dry_run=False):
    """Очистить договоры и связанные платежи"""
    if dry_run:
        cursor.execute("SELECT COUNT(*) FROM contracts")
        count = cursor.fetchone()[0]
        print_info(f"Будет удалено {count} договоров (и связанные платежи)")
        return count
    
    cursor.execute("DELETE FROM contracts")
    conn.commit()
    print_success("Договоры и платежи очищены")
    return 0

def clean_offices(cursor, conn, dry_run=False):
    """Очистить все офисы (удалить полностью)"""
    if dry_run:
        cursor.execute("SELECT COUNT(*) FROM offices")
        count = cursor.fetchone()[0]
        print_info(f"Будет удалено {count} офисов (ВНИМАНИЕ! Это удалит все связанные данные!)")
        return count
    
    # Сначала удаляем связанные данные (каскадно)
    cursor.execute("DELETE FROM office_views")
    cursor.execute("DELETE FROM applications")
    cursor.execute("DELETE FROM contracts")  # платежи удалятся каскадно
    cursor.execute("DELETE FROM offices")
    conn.commit()
    print_success("Все офисы и связанные данные удалены")
    return 0

def reset_offices_status(cursor, conn, dry_run=False):
    """Сбросить статус всех офисов на 'свободен'"""
    if dry_run:
        cursor.execute("SELECT COUNT(*) FROM offices WHERE is_free = FALSE")
        count = cursor.fetchone()[0]
        print_info(f"Будет изменено {count} офисов (статус на 'свободен')")
        return count
    
    cursor.execute("UPDATE offices SET is_free = TRUE")
    conn.commit()
    print_success("Статус всех офисов сброшен на 'свободен'")
    return 0

def clean_all_office_data(cursor, conn, dry_run=False):
    """Полная очистка всех данных по офисам (без удаления самих офисов)"""
    if dry_run:
        cursor.execute("SELECT COUNT(*) FROM office_views")
        views = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM applications")
        apps = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM contracts")
        contracts = cursor.fetchone()[0]
        print_info(f"Будет удалено:")
        print_info(f"   - {views} просмотров")
        print_info(f"   - {apps} заявок")
        print_info(f"   - {contracts} договоров (и платежи)")
        return views + apps + contracts
    
    cursor.execute("DELETE FROM office_views")
    cursor.execute("DELETE FROM applications")
    cursor.execute("DELETE FROM contracts")  # платежи удалятся каскадно
    conn.commit()
    print_success("Все данные по офисам (кроме самих офисов) очищены")
    return 0

def main():
    parser = argparse.ArgumentParser(description='Очистка данных по офисам')
    parser.add_argument('--all', action='store_true', help='Очистить все данные (кроме офисов)')
    parser.add_argument('--views', action='store_true', help='Очистить только просмотры')
    parser.add_argument('--applications', action='store_true', help='Очистить только заявки')
    parser.add_argument('--contracts', action='store_true', help='Очистить договоры и платежи')
    parser.add_argument('--offices', action='store_true', help='Удалить ВСЕ офисы (ОСТОРОЖНО!)')
    parser.add_argument('--reset-status', action='store_true', help='Сбросить статус всех офисов на "свободен"')
    parser.add_argument('--force', action='store_true', help='Принудительное выполнение без подтверждения')
    parser.add_argument('--dry-run', action='store_true', help='Показать что будет удалено без фактического удаления')
    
    args = parser.parse_args()
    
    # Если нет аргументов, показать справку
    if not (args.all or args.views or args.applications or args.contracts or args.offices or args.reset_status):
        parser.print_help()
        print("\n" + "="*60)
        print("Примеры использования:")
        print("  python clean_offices_data.py --all --force         # Очистить все данные, кроме офисов")
        print("  python clean_offices_data.py --offices --force     # Удалить ВСЕ офисы")
        print("  python clean_offices_data.py --views               # Очистить просмотры")
        print("  python clean_offices_data.py --reset-status        # Сбросить статус офисов")
        print("  python clean_offices_data.py --all --dry-run       # Посмотреть что будет удалено")
        print("="*60)
        sys.exit(0)
    
    # Подключение к БД
    try:
        conn = psycopg.connect(
            host='db',
            port=5432,
            user='postgres',
            password='admin',
            dbname='project'
        )
        cursor = conn.cursor()
        print_success("Подключение к базе данных установлено")
    except Exception as e:
        print_error(f"Ошибка подключения: {e}")
        sys.exit(1)
    
    # Показываем текущую статистику
    print_header("ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ")
    stats = get_stats(cursor)
    print_stats(stats)
    
    # Особое предупреждение для удаления офисов
    if args.offices and not args.dry_run:
        print_warning("\n" + "="*60)
        print_warning("ВНИМАНИЕ! Вы собираетесь УДАЛИТЬ ВСЕ ОФИСЫ!")
        print_warning("Это действие НЕОБРАТИМО и удалит:")
        print_warning("  - Все офисы")
        print_warning("  - Все просмотры")
        print_warning("  - Все заявки")
        print_warning("  - Все договоры")
        print_warning("  - Все платежи")
        print_warning("="*60)
        
        if not args.force:
            response = input(f"\n{Colors.BOLD}{Colors.RED}Вы УВЕРЕНЫ? (yes/no): {Colors.RESET}")
            if response.lower() != 'yes':
                print_info("Операция отменена")
                cursor.close()
                conn.close()
                sys.exit(0)
    
    # Общее предупреждение для других операций
    elif not args.dry_run and not args.force and not args.offices:
        print_warning("\nВНИМАНИЕ! Это действие необратимо!")
        response = input(f"\n{Colors.BOLD}Вы уверены? (yes/no): {Colors.RESET}")
        if response.lower() != 'yes':
            print_info("Операция отменена")
            cursor.close()
            conn.close()
            sys.exit(0)
    
    print_header("ВЫПОЛНЕНИЕ ОПЕРАЦИЙ")
    
    try:
        total_affected = 0
        
        if args.offices:
            total_affected += clean_offices(cursor, conn, args.dry_run)
        else:
            if args.all:
                total_affected += clean_all_office_data(cursor, conn, args.dry_run)
                
            if args.views:
                total_affected += clean_office_views(cursor, conn, args.dry_run)
                
            if args.applications:
                total_affected += clean_applications(cursor, conn, args.dry_run)
                
            if args.contracts:
                total_affected += clean_contracts(cursor, conn, args.dry_run)
                
            if args.reset_status:
                total_affected += reset_offices_status(cursor, conn, args.dry_run)
        
        if args.dry_run:
            print_header("РЕЗУЛЬТАТЫ DRY-RUN")
            print_info(f"Будет затронуто {total_affected} записей")
            print_info("Никаких изменений в базу данных не внесено")
        else:
            print_header("РЕЗУЛЬТАТЫ ОЧИСТКИ")
            
            # Показываем новую статистику
            new_stats = get_stats(cursor)
            print_stats(new_stats)
            
            print_success("\nОчистка успешно завершена!")
            
    except Exception as e:
        print_error(f"Ошибка при выполнении: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print_info("Соединение с базой данных закрыто")

if __name__ == "__main__":
    main()