@echo off
echo ========================================
echo ЗАПУСК ПРОЕКТА
echo ========================================
docker-compose up -d

echo.
echo Ожидание запуска БД...
timeout /t 10 /nobreak >nul

echo.
echo Проверка статуса:
docker ps

echo.
echo API: http://localhost:8000/docs
echo.
pause