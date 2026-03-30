# C:\Vs Code\BusinessCenter\Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt из папки backend
COPY backend/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код из backend в /app
COPY backend/ .

# Копируем SQL файл
COPY backend/full_bd.sql .

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]