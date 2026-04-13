#!/bin/bash

# =====================================================
# 🚀 BUSINESS CENTER - УНИВЕРСАЛЬНЫЙ СТАРТЕР
# =====================================================
# Поддерживает: Linux, macOS, Windows (Git Bash / WSL)
# Запуск: ./starter.sh [--rebuild] [--no-front]
# =====================================================

set -e

# =====================================================
# 🎨 ЦВЕТА
# =====================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# =====================================================
# 📦 ПЕРЕМЕННЫЕ
# =====================================================
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

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
                echo -e "${YELLOW}⚠️  Режим пересборки${NC}"
                shift
                ;;
            --no-front)
                START_FRONT=false
                echo -e "${YELLOW}⚠️  Фронтенд не будет запущен${NC}"
                shift
                ;;
            --help)
                echo -e "${GREEN}Использование: ./starter.sh [--rebuild] [--no-front]${NC}"
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
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker не найден${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"
    
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose не найден${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker Compose: $(docker compose version)${NC}"
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git не найден${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Git: $(git --version)${NC}"
    
    echo -e "${GREEN}✅ Все зависимости установлены!${NC}"
}

# =====================================================
# 📁 СОЗДАНИЕ ПАПОК
# =====================================================
create_directories() {
    echo -e "\n${BLUE}📁 Создание директорий...${NC}"
    
    mkdir -p "$LOGS_DIR" "$DATA_DIR/models" "$DATA_DIR/cache"
    
    echo -e "${GREEN}✅ Директории готовы${NC}"
}

# =====================================================
# 🔐 .env
# =====================================================
setup_env() {
    echo -e "\n${BLUE}🔐 Настройка окружения...${NC}"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$ENV_EXAMPLE" ]]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            echo -e "${GREEN}✅ Создан .env${NC}"
        else
            echo -e "${RED}❌ .env.example не найден${NC}"
            exit 1
        fi
    else
        echo -e "${CYAN}📄 .env уже существует${NC}"
    fi
}

# =====================================================
# 🐳 DOCKER
# =====================================================
start_docker() {
    echo -e "\n${BLUE}🐳 Запуск Docker-контейнеров...${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [[ "$REBUILD" == true ]]; then
        echo -e "${YELLOW}⚠️  Очистка старых контейнеров...${NC}"
        docker compose down -v 2>/dev/null || true
        docker rmi businesscenter-api 2>/dev/null || true
        docker compose build --no-cache
    else
        docker compose build
    fi
    
    docker compose up -d
    
    echo -e "\n${BLUE}📊 Статус контейнеров:${NC}"
    docker compose ps
    
    # Ожидание готовности API
    echo -e "${YELLOW}⏳ Ожидание готовности API...${NC}"
    local max_attempts=60
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API готов!${NC}"
            return 0
        fi
        sleep 1
        ((attempt++))
        echo -n "."
    done
    
    echo -e "\n${RED}❌ API не запустился за $max_attempts секунд${NC}"
    echo -e "${YELLOW}📖 Проверьте логи: docker compose logs api${NC}"
    exit 1
}

# =====================================================
# 🗄️ БД
# =====================================================
init_database() {
    echo -e "\n${BLUE}🗄️ Инициализация базы данных...${NC}"
    
    local sql_file="$PROJECT_ROOT/database/init.sql"
    
    if [[ ! -f "$sql_file" ]]; then
        echo -e "${RED}❌ $sql_file не найден${NC}"
        exit 1
    fi
    
    docker cp "$sql_file" business_center_db:/tmp/init.sql
    docker exec -i business_center_db psql -U postgres -d project -f /tmp/init.sql 2>&1 | grep -v "NOTICE" || true
    
    echo -e "${GREEN}✅ База данных готова${NC}"
}

# =====================================================
# 📊 ГЕНЕРАЦИЯ ДАННЫХ
# =====================================================
generate_data() {
    echo -e "\n${BLUE}📊 Генерация тестовых данных...${NC}"
    
    local generator="$PROJECT_ROOT/scripts/generate_advanced_data.py"
    
    if [[ ! -f "$generator" ]]; then
        echo -e "${YELLOW}⚠️  Генератор не найден, пропускаем${NC}"
        return
    fi
    
    docker cp "$generator" business_center_api:/app/scripts/generate_advanced_data.py
    docker exec -it business_center_api python /app/scripts/generate_advanced_data.py
    
    echo -e "${GREEN}✅ Данные сгенерированы${NC}"
}

# =====================================================
# 🤖 AI МОДЕЛЬ
# =====================================================
train_model() {
    echo -e "\n${BLUE}🤖 Обучение AI модели...${NC}"
    
    docker exec -i business_center_api python -c "
from api.ml_models.office_rental_prediction import rental_predictor
from api.database import get_db
conn = get_db()
result = rental_predictor.train(conn, force_retrain=True)
print('✅ Модель обучена' if result.get('status') != 'error' else '⚠️ Ошибка обучения')
conn.close()
" 2>&1 | grep -v "NotOpenSSLWarning" || true
    
    echo -e "${GREEN}✅ Модель готова${NC}"
}

# =====================================================
# 🖥️ ФРОНТЕНД
# =====================================================
start_frontend() {
    if [[ "$START_FRONT" == false ]]; then
        return
    fi
    
    echo -e "\n${BLUE}🖥️ Запуск фронтенда...${NC}"
    
    local frontend_dir="$PROJECT_ROOT/frontend"
    
    if [[ ! -d "$frontend_dir" ]]; then
        echo -e "${YELLOW}⚠️  Папка фронтенда не найдена${NC}"
        return
    fi
    
    cd "$frontend_dir"
    
    if [[ -f "package.json" ]]; then
        if [[ ! -d "node_modules" ]]; then
            echo -e "${YELLOW}📦 Установка зависимостей npm...${NC}"
            npm install
        fi
        echo -e "${GREEN}🚀 Запуск React-приложения...${NC}"
        npm start &
    else
        if command -v npx &> /dev/null; then
            echo -e "${GREEN}🚀 Запуск Live Server...${NC}"
            npx live-server --port=3000 --no-browser &
        else
            echo -e "${YELLOW}⚠️  npx не найден, откройте файлы вручную${NC}"
        fi
    fi
    
    cd "$PROJECT_ROOT"
}

# =====================================================
# 📊 ИТОГИ
# =====================================================
print_summary() {
    echo -e "\n${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}✅ СТАРТ ЗАВЕРШЕН УСПЕШНО!${NC}"
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}🔗 Доступные сервисы:${NC}"
    echo -e "   📡 API Documentation: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "   🐘 pgAdmin:           ${BLUE}http://localhost:8080${NC} (admin@admin.com / admin)"
    echo -e "   🗄️  PostgreSQL:        ${BLUE}localhost:5432${NC}"
    echo -e "   🔄 Redis:             ${BLUE}localhost:6379${NC}"
    
    if [[ "$START_FRONT" == true ]]; then
        echo -e "   🖥️  Фронтенд:          ${BLUE}http://localhost:3000${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}📖 Полезные команды:${NC}"
    echo -e "   docker compose logs api      - логи API"
    echo -e "   docker compose down          - остановка"
    echo -e "   ./starter.sh --rebuild       - полная пересборка"
    echo ""
    echo -e "${GREEN}👤 Тестовые пользователи:${NC}"
    echo -e "   admin / admin123   (Admin)"
    echo -e "   manager / manager123 (Manager)"
    echo -e "   client / client123  (Client)"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
}

# =====================================================
# 🎬 MAIN
# =====================================================
main() {
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}         🏢 BUSINESS CENTER - УНИВЕРСАЛЬНЫЙ СТАРТЕР        ${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    
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

main "$@"