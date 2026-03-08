# Базовый образ Python
FROM python:3.12-slim

# Рабочая директория в контейнере
WORKDIR /app

# Устанавливаем зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY backend/ ./backend/

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["python", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]