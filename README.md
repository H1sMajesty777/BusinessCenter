# 🏢 Business Center - AI система управления арендой офисов

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis)
![Docker](https://img.shields.io/badge/Docker-✓-blue?logo=docker)
![ML](https://img.shields.io/badge/ML-ScikitLearn-orange)

**Система для прогнозирования аренды офисов с использованием машинного обучения**

[Документация API](#-api-endpoints) • [Установка](#-быстрый-старт) • [ML модель](#-ml-модель)

</div>

---

## 📋 О проекте

Business Center - это комплексная система для управления арендой офисных помещений с интегрированным **AI модулем** для прогнозирования вероятности аренды.

### 🎯 Основные возможности

- ✅ Управление офисами (CRUD операции)
- ✅ Управление пользователями и ролями (Admin, Manager, Client)
- ✅ Обработка заявок на аренду
- ✅ Учёт договоров и платежей
- ✅ **ML прогнозирование** вероятности аренды
- ✅ JWT аутентификация с refresh токенами
- ✅ Redis для токенов и кэширования
- ✅ Swagger документация API

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/H1sMajesty777/BusinessCenter
cd BusinessCenter
2. Подготовка директорий
bash
mkdir -p data/models data/cache logs/ml
3. Сборка и запуск
bash
# Полная пересборка с зависимостями (рекомендуется при первом запуске)
docker-compose build --no-cache

# Запуск контейнеров
docker-compose up -d
Ожидаемый вывод:

text
business_center_db      - PostgreSQL 16 (порт 5432)
business_center_redis   - Redis 7 (порт 6379)  
business_center_api     - FastAPI (порт 8000)
business_center_pgadmin - pgAdmin 4 (порт 8080)
4. Инициализация базы данных
bash
# Копирование SQL скрипта
docker cp full_bd.sql business_center_db:/tmp/init.sql

# Выполнение инициализации
docker exec -it business_center_db psql -U postgres -d project -f /tmp/init.sql
5. Генерация тестовых данных
bash
# Копирование генератора данных
docker cp generate_advanced_data.py business_center_api:/app/generate_advanced_data.py

# Запуск генерации
docker exec -it business_center_api python /app/generate_advanced_data.py
6. Копирование ML модуля
bash
# Копирование моделей машинного обучения
docker cp backend/api/ml_models business_center_api:/app/api/

# Копирование скрипта инициализации
docker cp scripts/init_ml.py business_center_api:/app/scripts/
7. Обучение AI модели
bash
# Запуск обучения (зависимости уже есть в образе!)
docker exec -it business_center_api python /app/scripts/init_ml.py --force

### 5. Получение токена доступа

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","password":"admin123"}'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 6. Обучение ML модели

```bash
# Замените YOUR_TOKEN на полученный access_token
curl -X POST "http://localhost:8000/api/ai/rental-prediction/train?force=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Ожидаемый ответ:**
```json
{
  "success": true,
  "details": {
    "status": "trained",
    "accuracy": 1.0,
    "roc_auc": 1.0,
    "samples_used": 23
  }
}
```

### 7. Получение прогнозов

```bash
# Прогноз для конкретного офиса
curl -X GET "http://localhost:8000/api/ai/rental-prediction/office/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Сводка по всем свободным офисам
curl -X GET "http://localhost:8000/api/ai/rental-prediction/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 API Endpoints

### 🔐 Аутентификация
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/login` | Вход в систему |
| POST | `/api/auth/refresh` | Обновление токена |
| POST | `/api/auth/logout` | Выход |
| GET | `/api/auth/me` | Профиль пользователя |

### 🏢 Офисы
| Метод | URL | Описание | Доступ |
|-------|-----|----------|--------|
| GET | `/api/offices` | Список офисов | Все |
| GET | `/api/offices/{id}` | Детали офиса | Все |
| POST | `/api/offices` | Создать офис | Admin/Manager |
| PUT | `/api/offices/{id}` | Обновить офис | Admin/Manager |
| DELETE | `/api/offices/{id}` | Удалить офис | Admin/Manager |

### 📝 Заявки
| Метод | URL | Описание | Доступ |
|-------|-----|----------|--------|
| GET | `/api/applications` | Все заявки | Admin/Manager |
| GET | `/api/applications/my` | Мои заявки | Client |
| POST | `/api/applications` | Создать заявку | Client |
| PUT | `/api/applications/{id}/status` | Обновить статус | Admin/Manager |

### 🤖 AI Прогнозирование
| Метод | URL | Описание | Доступ |
|-------|-----|----------|--------|
| POST | `/api/ai/rental-prediction/train` | Обучение модели | Admin |
| GET | `/api/ai/rental-prediction/office/{id}` | Прогноз для офиса | Все |
| GET | `/api/ai/rental-prediction/summary` | Сводка прогнозов | Admin/Manager |
| GET | `/api/ai/rental-prediction/explain/{id}` | Объяснение прогноза | Admin/Manager |
| GET | `/api/ai/rental-prediction/trends` | Тренды аренды | Admin/Manager |

### 👥 Пользователи
| Метод | URL | Описание | Доступ |
|-------|-----|----------|--------|
| GET | `/api/users` | Список пользователей | Admin |
| GET | `/api/users/{id}` | Данные пользователя | Admin/Self |
| POST | `/api/users/register` | Регистрация | Все |
| PUT | `/api/users/me` | Обновить профиль | Client |
| DELETE | `/api/users/{id}` | Удалить пользователя | Admin |

---

## 🧠 ML Модель

### Архитектура (Ансамбль из 5 моделей)

```
├── RandomForestClassifier (100 деревьев)
├── GradientBoostingClassifier (100 деревьев)  
└── Ансамбль (усреднение вероятностей)
```

### Признаки для обучения (19 параметров)

| Категория | Признаки |
|-----------|----------|
| **Офис** | этаж, площадь, цена, цена за м², статус |
| **Просмотры** | всего, уникальных, за 7/30/90 дней, средняя длительность, конверсия в контакт |
| **Заявки** | всего, процент одобрения, давность последней |
| **Договоры** | всего, средняя сумма, средняя длительность, активные |
| **Конкуренция** | доля свободных на этаже, средняя цена на этаже |

### Важность признаков

```
1. contract_count         ████████████████████ 23.4%
2. avg_contract_amount    ███████████████████  22.4%
3. has_active_contract    █████████████████    18.9%
4. views_last_7d          ████                  5.2%
5. view_count             ████                  4.8%
```

### Пример ответа модели

```json
{
  "office_id": 1,
  "probability": 0.9549,
  "probability_percent": 95.5,
  "category": "high",
  "description": "Высокая вероятность аренды в этом месяце",
  "top_factors": [
    {"feature": "contract_count", "importance": 0.2338},
    {"feature": "avg_contract_amount", "importance": 0.2243},
    {"feature": "has_active_contract", "importance": 0.1898}
  ],
  "recommendations": [
    "🎯 Высокий спрос на офис!",
    "⚡ Действуйте быстро: подготовьте договор",
    "💰 Возможно повышение цены на 5-10%"
  ]
}
```

### ⚠️ Важное замечание о качестве модели

Текущая версия модели на **синтетических тестовых данных** показывает:
- **Accuracy: 100%**
- **AUC ROC: 1.000**

**В реальных условиях** с реальными данными метрики будут ниже (обычно 0.70-0.85). Идеальные метрики на тестовых данных - следствие:
- Использования синтетических данных
- Небольшого объёма обучающей выборки
- Отсутствия шума в данных

---

## 🗄️ Доступные сервисы

| Сервис | URL | Данные для входа |
|--------|-----|------------------|
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **pgAdmin** | http://localhost:8080 | `admin@admin.com` / `admin` |
| **PostgreSQL** | `localhost:5432` | `postgres` / `admin` |
| **Redis** | `localhost:6379` | - |

---

## 👤 Тестовые пользователи

| Логин | Пароль | Роль | Описание |
|-------|--------|------|----------|
| `admin` | `admin123` | **Admin** | Полный доступ |
| `manager` | `manager123` | **Manager** | Управление офисами |
| `client` | `client123` | **Client** | Арендатор |

---

## 📁 Структура проекта

```
BusinessCenter/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # Точка входа FastAPI
│   │   ├── config.py            # Настройки приложения
│   │   ├── database.py          # Подключение к БД и Redis
│   │   ├── security.py          # JWT и хеширование
│   │   ├── models/              # Pydantic модели
│   │   │   ├── user.py
│   │   │   ├── office.py
│   │   │   ├── application.py
│   │   │   ├── contract.py
│   │   │   └── payment.py
│   │   ├── routers/             # API эндпоинты
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── offices.py
│   │   │   ├── applications.py
│   │   │   ├── contracts.py
│   │   │   ├── payments.py
│   │   │   ├── office_views.py
│   │   │   ├── audit.py
│   │   │   └── ai_rental_prediction.py
│   │   └── ml_models/           # ML модели
│   │       └── office_rental_prediction.py
│   └── requirements.txt
├── full_bd.sql                  # Схема базы данных
├── docker-compose.yml           # Docker оркестрация
├── Dockerfile                   # Сборка API образа
├── generate_advanced_data.py    # Генератор тестовых данных
└── README.md                    # Документация
```

---

## 🔧 Команды управления

### Запуск проекта
```bash
docker-compose up -d
```

### Остановка проекта
```bash
docker-compose down
```

### Перезапуск API
```bash
docker-compose restart api
```

### Просмотр логов
```bash
docker-compose logs api
docker-compose logs db
```

### Полная очистка (пересборка с нуля)
```bash
docker-compose down -v
docker rmi businesscenter-api
docker build -t businesscenter-api .
docker-compose up -d
```

### Вход в контейнеры
```bash
# Вход в API контейнер
docker exec -it business_center_api bash

# Вход в PostgreSQL
docker exec -it business_center_db psql -U postgres -d project

# Вход в Redis
docker exec -it business_center_redis redis-cli
```

---

## 🛠️ Технологии

| Компонент | Технология | Версия |
|-----------|------------|--------|
| **Backend** | FastAPI | 0.115.6 |
| **Database** | PostgreSQL | 16 |
| **Cache** | Redis | 7 |
| **ML** | Scikit-learn | 1.3.0 |
| **Auth** | JWT + bcrypt | - |
| **Container** | Docker | 24+ |

### Python зависимости
```
fastapi, uvicorn, pydantic, psycopg, redis,
python-jose, passlib, bcrypt, python-dotenv,
numpy, pandas, scikit-learn, joblib
```

---

## 📈 Планы развития

- [ ] Добавить реальные данные от 1С/CRM
- [ ] Внедрить Deep Learning (PyTorch)
- [ ] Добавить A/B тестирование моделей
- [ ] Создать дашборд с визуализацией
- [ ] Добавить уведомления (Telegram/Email)
- [ ] Интеграция с платежными системами
- [ ] Мобильное приложение

---

## 📄 Лицензия

MIT License

---

## 👨‍💻 Автор

**H1sMajesty777**

- GitHub: [@H1sMajesty777](https://github.com/H1sMajesty777)

**Albert342545346**

- GitHub: [Albert342545346](https://github.com/Albert342545346)


---

## ⭐ Если проект оказался полезным

Поставь звезду на GitHub и поделись с коллегами!

```