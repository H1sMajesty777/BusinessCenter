#!/bin/bash

echo "=========================================="
echo "   Business Center - Полный запуск"
echo "=========================================="

# Переходим в корень проекта
cd "$(dirname "$0")"

# Создаём необходимые папки
echo " Создаём папки для данных..."
mkdir -p data/models data/cache logs/ml

# Проверяем наличие .env
if [ ! -f .env ]; then
    echo " Файл .env не найден!"
    echo "Создайте .env файл в корне проекта"
    exit 1
fi

# Останавливаем старые контейнеры
echo " Останавливаем старые контейнеры..."
docker-compose down -v 2>/dev/null

# Собираем и запускаем
echo " Собираем образы..."
docker-compose build --no-cache

echo " Запускаем контейнеры..."
docker-compose up -d

# Ждём запуска БД
echo " Ожидаем запуск PostgreSQL..."
sleep 15

# Проверяем здоровье БД
echo " Проверяем подключение к БД..."
until docker exec business_center_db pg_isready -U postgres; do
    echo "Ждём БД..."
    sleep 2
done

# Инициализируем БД
echo " Инициализируем базу данных..."
docker exec -i business_center_db psql -U postgres -d project < full_bd.sql 2>/dev/null

if [ $? -eq 0 ]; then
    echo " База данных инициализирована"
else
    echo " База данных уже была инициализирована"
fi

# Копируем и запускаем генератор данных
echo " Генерируем тестовые данные..."
docker cp generate_advanced_data.py business_center_api:/app/generate_advanced_data.py
docker exec business_center_api python /app/generate_advanced_data.py

echo ""
echo "=========================================="
echo " СИСТЕМА ГОТОВА!"
echo "=========================================="
echo ""
echo " Доступные сервисы:"
echo "    API Docs:      http://localhost:8000/docs"
echo "    pgAdmin:       http://localhost:8080 (admin@admin.com / admin)"
echo ""
echo " Тестовые пользователи:"
echo "    admin    / admin123"
echo "    manager  / manager123"
echo "    client   / client123"
echo ""
echo " Для обучения ML модели:"
echo ""
echo "   Получите токен:"
echo "   curl -X POST http://localhost:8000/api/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"login\":\"admin\",\"password\":\"admin123\"}' \\"
echo "     -c cookies.txt"
echo ""
echo "   Обучите модель:"
echo "   curl -X POST 'http://localhost:8000/api/ai/rental-prediction/train?force=true' \\"
echo "     -b cookies.txt"
echo ""
echo "   Получите прогноз:"
echo "   curl -X GET http://localhost:8000/api/ai/rental-prediction/office/1 \\"
echo "     -b cookies.txt"
echo ""
echo "=========================================="