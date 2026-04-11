FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для компиляции ML библиотек
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    cmake \
    libpq-dev \
    libopenblas-dev \
    liblapack-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY backend/requirements.txt .

# Установка Python зависимостей (сначала numpy для оптимизации)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir scipy==1.11.4 && \
    pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY backend/ .

# Создаём директории для ML моделей
RUN mkdir -p /app/data/models /app/data/cache /app/logs/ml

# Создать папку для скриптов
RUN mkdir -p /app/scripts

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]