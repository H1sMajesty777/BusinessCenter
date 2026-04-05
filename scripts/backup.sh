#!/bin/bash

# ============================================
# Бэкап PostgreSQL для Business Center
# ============================================

# Настройки
BACKUP_DIR="./backups"
LOG_FILE="./logs/backup.log"
DB_CONTAINER="business_center_db"
DB_USER="postgres"
DB_NAME="project"
RETENTION_DAYS=30
KEEP_LAST_N=10

# Создаем директории
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Текущая дата и время
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"
BACKUP_GZIP="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

echo "=========================================" >> "$LOG_FILE"
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Начало бэкапа" >> "$LOG_FILE"

# Проверка, что контейнер запущен
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] ОШИБКА: Контейнер $DB_CONTAINER не запущен!" >> "$LOG_FILE"
    exit 1
fi

# Создание бэкапа (сжатие на лету)
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Создание бэкапа..." >> "$LOG_FILE"
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" 2>> "$LOG_FILE" | gzip > "$BACKUP_GZIP"

# Проверка, что бэкап создан
if [ -f "$BACKUP_GZIP" ] && [ -s "$BACKUP_GZIP" ]; then
    SIZE=$(du -h "$BACKUP_GZIP" | cut -f1)
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] Бэкап создан: $BACKUP_GZIP ($SIZE)" >> "$LOG_FILE"
    
    # Создаем MD5 хеш для проверки целостности
    md5sum "$BACKUP_GZIP" > "$BACKUP_GZIP.md5"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] MD5 хеш: $(cat "$BACKUP_GZIP.md5")" >> "$LOG_FILE"
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] ОШИБКА: Бэкап не создан!" >> "$LOG_FILE"
    exit 1
fi

# Удаление старых бэкапов (по дате)
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Удаление бэкапов старше $RETENTION_DAYS дней..." >> "$LOG_FILE"
find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "backup_*.sql.gz.md5" -type f -mtime +$RETENTION_DAYS -delete

# Дополнительно: оставляем только последние N бэкапов (на всякий случай)
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Оставляем только последние $KEEP_LAST_N бэкапов..." >> "$LOG_FILE"
ls -1t "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | tail -n +$((KEEP_LAST_N + 1)) | xargs rm -f 2>/dev/null
ls -1t "$BACKUP_DIR"/backup_*.sql.gz.md5 2>/dev/null | tail -n +$((KEEP_LAST_N + 1)) | xargs rm -f 2>/dev/null

# Итоговая статистика
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | wc -l)
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Бэкап завершен. Всего бэкапов: $BACKUP_COUNT" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"

echo "✅ Бэкап создан: $BACKUP_GZIP"
echo "📁 Всего бэкапов в директории: $BACKUP_COUNT"