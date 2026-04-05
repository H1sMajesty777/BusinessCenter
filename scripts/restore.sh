#!/bin/bash

# ============================================
# Восстановление PostgreSQL для Business Center
# ============================================

BACKUP_DIR="./backups"
LOG_FILE="./logs/restore.log"
DB_CONTAINER="business_center_db"
DB_USER="postgres"
DB_NAME="project"

# Поиск последнего бэкапа, если аргумент не передан
if [ -z "$1" ]; then
    BACKUP_FILE=$(ls -1t "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        echo " Нет бэкапов в директории $BACKUP_DIR"
        echo "Использование: ./scripts/restore.sh [путь_к_бэкапу.sql.gz]"
        exit 1
    fi
    echo " Использую последний бэкап: $BACKUP_FILE"
else
    BACKUP_FILE="$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Файл $BACKUP_FILE не найден"
        exit 1
    fi
fi

echo "========================================="
echo "Восстановление базы данных"
echo "========================================="
echo "Бэкап: $BACKUP_FILE"

# Проверка MD5
if [ -f "$BACKUP_FILE.md5" ]; then
    echo "Проверка целостности бэкапа..."
    cd "$BACKUP_DIR"
    md5sum -c "$(basename "$BACKUP_FILE.md5")" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "ОШИБКА: Бэкап поврежден!"
        exit 1
    fi
    cd - > /dev/null
    echo "Бэкап целостен"
fi

# Подтверждение
echo ""
read -p "Восстановление удалит текущие данные. Продолжить? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено"
    exit 1
fi

echo "Восстановление..."

# Останавливаем приложение (опционально)
docker-compose stop api 2>/dev/null

# Сбрасываем и восстанавливаем БД
gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" 2>&1

if [ $? -eq 0 ]; then
    echo " База данных восстановлена из $BACKUP_FILE"
    # Запускаем API обратно
    docker-compose start api 2>/dev/null
else
    echo " ОШИБКА при восстановлении"
    exit 1
fi

echo "========================================="
echo "Готово!"