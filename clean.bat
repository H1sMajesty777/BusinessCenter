@echo off
echo ========================================
echo ОСТАНОВКА И УДАЛЕНИЕ ВСЕХ КОНТЕЙНЕРОВ
echo ========================================
docker-compose down -v

echo.
echo ========================================
echo УДАЛЕНИЕ ОБРАЗА
echo ========================================
docker rmi businesscenter-api 2>nul

echo.
echo ========================================
echo СБОРКА НОВОГО ОБРАЗА
echo ========================================
docker build --no-cache -t businesscenter-api .

echo.
echo ========================================
echo ЗАПУСК КОНТЕЙНЕРОВ
echo ========================================
docker-compose up -d

echo.
echo ========================================
echo ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
echo ========================================
timeout /t 10 /nobreak >nul
docker exec -i business_center_db psql -U postgres -d project < full_bd.sql

echo.
echo ========================================
echo ГОТОВО!
echo ========================================
echo API доступен: http://localhost:8000/docs
echo pgAdmin: http://localhost:8080 (admin@admin.com / admin)
echo.
pause