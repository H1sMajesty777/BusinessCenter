#!/bin/bash

# =====================================================
# 🚀 BUSINESS CENTER - УНИВЕРСАЛЬНЫЙ СТАРТЕР
# =====================================================
# Поддерживает: Linux, macOS, Windows (Git Bash / WSL)
# Запуск: ./start.sh [--rebuild] [--no-front]
# =====================================================

set -e  # Останавливаем скрипт при любой ошибке

# =====================================================
# 🎨 ЦВЕТА ДЛЯ ВЫВОДА (работают во всех терминалах)
# =====================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# =====================================================
# 📦 ПЕРЕМЕННЫЕ
# =====================================================
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOGS_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

# Флаги
REBUILD=false
START_FRONT=true

# =====================================================
# 🖥️ ОПРЕДЕЛЕНИЕ ОС
# =====================================================
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    elif [[ -n "$WSLENV" ]] || [[ -n "$WSL_DISTRO_NAME" ]]; then
        OS="wsl"
    else
        OS="unknown"
    fi
    echo -e "${CYAN}📌 Определена ОС: $OS${NC}"
}

# =====================================================
# 📝 ПАРСИНГ АРГУМЕНТОВ
# =====================================================
parse_args() {
    for arg in "$@"; do
        case $arg in
            --rebuild)
                REBUILD=true
                echo -e "${YELLOW}⚠️  Режим пересборки: будут удалены старые контейнеры и образы${NC}"
                shift
                ;;
            --no-front)
                START_FRONT=false
                echo -e "${YELLOW}⚠️  Фронтенд запускаться не будет${NC}"
                shift
                ;;
            --help)
                echo -e "${GREEN}Использование: ./start.sh [--rebuild] [--no-front]${NC}"
                echo "  --rebuild    - Полная пересборка Docker-образов"
                echo "  --no-front   - Не запускать фронтенд (только бэкенд)"
                exit 0
                ;;
        esac
    done
}

# =====================================================
# ✅ ПРОВЕРКА ЗАВИСИМОСТЕЙ
# =====================================================
check_dependencies() {
    echo -e "\n${BLUE}🔍 Проверка зависимостей...${NC}"
    
    local missing=()
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        missing+=("Docker")
    else
        echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"
    fi
    
    # Проверка Docker Compose
    if ! docker compose version &> /dev/null; then
        missing+=("Docker Compose")
    else
        echo -e "${GREEN}✅ Docker Compose: $(docker compose version)${NC}"
    fi
    
    # Проверка Git
    if ! command -v git &> /dev/null; then
        missing+=("Git")
    else
        echo -e "${GREEN}✅ Git: $(git --version)${NC}"
    fi
    
    # Проверка Node.js (только если нужен фронт)
    if [[ "$START_FRONT" == true ]]; then
        if ! command -v node &> /dev/null; then
            echo -e "${YELLOW}⚠️  Node.js не найден. Фронтенд будет запущен через Live Server (если установлен)${NC}"
        else
            echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"
        fi
        
        # Проверка npx (для live-server)
        if ! command -v npx &> /dev/null; then
            echo -e "${YELLOW}⚠️  npx не найден. Установите Node.js или запустите фронт вручную${NC}"
        fi
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Отсутствуют обязательные зависимости: ${missing[*]}${NC}"
        echo -e "${YELLOW}📖 Установите их и повторите запуск.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Все зависимости установлены!${NC}"
}

# =====================================================
# 📁 СОЗДАНИЕ НЕОБХОДИМЫХ ПАПОК
# =====================================================
create_directories() {
    echo -e "\n${BLUE}📁 Создание директорий...${NC}"
    
    local dirs=("$LOGS_DIR" "$DATA_DIR/models" "$DATA_DIR/cache")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            echo -e "${GREEN}✅ Создана: $dir${NC}"
        else
            echo -e "${CYAN}📁 Уже существует: $dir${NC}"
        fi
    done
}

# =====================================================
# 🔐 НАСТРОЙКА .env
# =====================================================
setup_env() {
    echo -e "\n${BLUE}🔐 Настройка окружения...${NC}"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$ENV_EXAMPLE" ]]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            echo -e "${GREEN}✅ Создан .env из .env.example${NC}"
            echo -e "${YELLOW}⚠️  Проверьте и при необходимости отредактируйте .env${NC}"
        else
            echo -e "${RED}❌ Файл .env.example не найден!${NC}"
            exit 1
        fi
    else
        echo -e "${CYAN}📄 .env уже существует${NC}"
    fi
}

# =====================================================
# 🐳 ЗАПУСК DOCKER
# =====================================================
start_docker() {
    echo -e "\n${BLUE}🐳 Запуск Docker-контейнеров...${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [[ "$REBUILD" == true ]]; then
        echo -e "${YELLOW}⚠️  Останавливаем и удаляем старые контейнеры...${NC}"
        docker compose down -v 2>/dev/null || true
        
        echo -e "${YELLOW}⚠️  Удаляем старый образ...${NC}"
        docker rmi businesscenter-api 2>/dev/null || true
        
        echo -e "${BLUE}🔨 Сборка образов с --no-cache...${NC}"
        docker compose build --no-cache
    else
        echo -e "${BLUE}🔨 Сборка образов...${NC}"
        docker compose build
    fi
    
    echo -e "${BLUE}🚀 Запуск контейнеров...${NC}"
    docker compose up -d
    
    # Проверка статуса контейнеров
    echo -e "\n${BLUE}📊 Статус контейнеров:${NC}"
    docker compose ps
    
    # Ожидание готовности API
    echo -e "${YELLOW}⏳ Ожидание готовности API (максимум 30 сек)...${NC}"
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API готов!${NC}"
            break
        fi
        sleep 1
        ((attempt++))
        echo -n "."
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        echo -e "${RED}❌ API не запустился за $max_attempts секунд${NC}"
        echo -e "${YELLOW}📖 Проверьте логи: docker compose logs api${NC}"
        exit 1
    fi
}

# =====================================================
# 🗄️ ИНИЦИАЛИЗАЦИЯ БД
# =====================================================
init_database() {
    echo -e "\n${BLUE}🗄️ Инициализация базы данных...${NC}"
    
    local sql_file="$PROJECT_ROOT/database/init.sql"
    
    if [[ ! -f "$sql_file" ]]; then
        echo -e "${RED}❌ Файл $sql_file не найден!${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}📤 Копирование SQL-скрипта в контейнер...${NC}"
    docker cp "$sql_file" business_center_db:/tmp/init.sql
    
    echo -e "${BLUE}⚙️ Выполнение инициализации...${NC}"
    docker exec -i business_center_db psql -U postgres -d project -f /tmp/init.sql 2>&1 | grep -v "NOTICE" || true
    
    echo -e "${GREEN}✅ База данных инициализирована${NC}"
}

# =====================================================
# 📊 ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ
# =====================================================
generate_data() {
    echo -e "\n${BLUE}📊 Генерация тестовых данных...${NC}"
    
    local generator="$PROJECT_ROOT/scripts/generate_advanced_data.py"
    
    if [[ ! -f "$generator" ]]; then
        echo -e "${YELLOW}⚠️  Генератор не найден: $generator${NC}"
        echo -e "${YELLOW}📖 Пропускаем генерацию данных.${NC}"
        return
    fi
    
    echo -e "${BLUE}📤 Копирование генератора в контейнер...${NC}"
    docker cp "$generator" business_center_api:/app/scripts/generate_advanced_data.py
    
    echo -e "${BLUE}⚙️ Запуск генерации...${NC}"
    docker exec -it business_center_api python /app/scripts/generate_advanced_data.py
    
    echo -e "${GREEN}✅ Тестовые данные сгенерированы${NC}"
}

# =====================================================
# 🤖 ОБУЧЕНИЕ AI МОДЕЛИ
# =====================================================
train_model() {
    echo -e "\n${BLUE}🤖 Обучение AI модели...${NC}"
    
    echo -e "${BLUE}⚙️ Запуск обучения через API...${NC}"
    
    # Получаем токен админа
    local login_response=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"login":"admin","password":"admin123"}')
    
    local token=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [[ -z "$token" ]]; then
        echo -e "${RED}❌ Не удалось получить токен администратора${NC}"
        echo -e "${YELLOW}📖 Возможно, пользователь admin не создан в БД${NC}"
        return
    fi
    
    echo -e "${BLUE}🚀 Запуск обучения модели...${NC}"
    local train_response=$(curl -s -X POST "http://localhost:8000/api/ai/rental-prediction/train?force=true" \
        -H "Authorization: Bearer $token")
    
    if echo "$train_response" | grep -q '"status":"trained"'; then
        echo -e "${GREEN}✅ Модель успешно обучена!${NC}"
    else
        echo -e "${YELLOW}⚠️  Обучение модели завершилось с предупреждением:${NC}"
        echo "$train_response"
    fi
}

# =====================================================
# 🖥️ ЗАПУСК ФРОНТЕНДА
# =====================================================
start_frontend() {
    if [[ "$START_FRONT" == false ]]; then
        echo -e "\n${CYAN}🚫 Фронтенд не запущен (флаг --no-front)${NC}"
        return
    fi
    
    echo -e "\n${BLUE}🖥️ Запуск фронтенда...${NC}"
    
    if [[ ! -d "$FRONTEND_DIR" ]]; then
        echo -e "${RED}❌ Папка фронтенда не найдена: $FRONTEND_DIR${NC}"
        return
    fi
    
    cd "$FRONTEND_DIR"
    
    # Проверяем наличие package.json (React/Vue проект)
    if [[ -f "package.json" ]]; then
        if [[ ! -d "node_modules" ]]; then
            echo -e "${BLUE}📦 Установка зависимостей npm...${NC}"
            npm install
        fi
        echo -e "${GREEN}🚀 Запуск React/Vue приложения...${NC}"
        npm start &
    else
        # Используем live-server для статических HTML-файлов
        if command -v npx &> /dev/null; then
            echo -e "${GREEN}🚀 Запуск Live Server...${NC}"
            npx live-server --port=3000 --no-browser &
        else
            echo -e "${YELLOW}⚠️  npx не найден. Фронтенд не запущен.${NC}"
            echo -e "${YELLOW}📖 Установите Node.js или откройте файлы вручную: $FRONTEND_DIR/index.html${NC}"
        fi
    fi
    
    cd "$PROJECT_ROOT"
}

# =====================================================
# 📊 ИТОГОВАЯ ИНФОРМАЦИЯ
# =====================================================
print_summary() {
    echo -e "\n${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}✅ СТАРТ ЗАВЕРШЕН УСПЕШНО!${NC}"
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}🔗 Доступные сервисы:${NC}"
    echo -e "   📡 API Documentation: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "   🐘 pgAdmin:           ${BLUE}http://localhost:8080${NC} (admin@admin.com / admin)"
    echo -e "   🗄️  PostgreSQL:        ${BLUE}localhost:5432${NC} (postgres / admin)"
    echo -e "   🔄 Redis:             ${BLUE}localhost:6379${NC}"
    
    if [[ "$START_FRONT" == true ]]; then
        echo -e "   🖥️  Фронтенд:          ${BLUE}http://localhost:3000${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}📖 Полезные команды:${NC}"
    echo -e "   docker compose logs api      - просмотр логов API"
    echo -e "   docker compose down          - остановка всех контейнеров"
    echo -e "   docker compose restart api   - перезапуск API"
    echo -e "   ./start.sh --rebuild         - полная пересборка"
    echo ""
    echo -e "${GREEN}👤 Тестовые пользователи:${NC}"
    echo -e "   admin / admin123   (Admin)"
    echo -e "   manager / manager123 (Manager)"
    echo -e "   client / client123  (Client)"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
}

# =====================================================
# 🔧 ОБРАБОТКА ОШИБОК
# =====================================================
handle_error() {
    local line=$1
    local command=$2
    local code=$3
    echo -e "\n${RED}${BOLD}❌ ОШИБКА НА ЭТАПЕ: ${command}${NC}"
    echo -e "${RED}   Строка: $line${NC}"
    echo -e "${RED}   Код ошибки: $code${NC}"
    echo -e "${YELLOW}📖 Попробуйте:${NC}"
    echo -e "   1. Проверить логи: docker compose logs"
    echo -e "   2. Перезапустить скрипт: ./start.sh --rebuild"
    echo -e "   3. Обратиться к документации README.md"
    exit $code
}

# =====================================================
# 🎬 MAIN
# =====================================================
main() {
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}         🏢 BUSINESS CENTER - УНИВЕРСАЛЬНЫЙ СТАРТЕР        ${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    
    # Перехват ошибок
    trap 'handle_error $LINENO "$BASH_COMMAND" $?' ERR
    
    detect_os
    parse_args "$@"
    check_dependencies
    create_directories
    setup_env
    start_docker
    init_database
    generate_data
    train_model
    start_frontend
    print_summary
}

# Запуск
main "$@"