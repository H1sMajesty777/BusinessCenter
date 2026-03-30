FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip
RUN pip install --upgrade pip

# Копируем requirements и устанавливаем зависимости ПО СЛОЯМ
COPY backend/requirements.txt .

# Устанавливаем базовые зависимости (без ML)
RUN pip install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn==0.34.0 \
    python-multipart==0.0.20 \
    pydantic==2.10.4 \
    pydantic-settings==2.7.0 \
    psycopg[binary]==3.1.19 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    bcrypt==4.0.1 \
    python-dotenv==1.0.1 \
    redis==5.2.1

# Устанавливаем ML зависимости (отдельно для кэширования)
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    pandas==2.0.3 \
    scikit-learn==1.3.0 \
    joblib==1.3.2

# Копируем код
COPY backend/ .
COPY backend/full_bd.sql .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]