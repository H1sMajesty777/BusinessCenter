-- БИЗНЕС-ЦЕНТР: База данных (чистый UTF-8)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

INSERT INTO roles (name, description) VALUES 
('admin', 'Полный доступ к системе'),
('manager', 'Управление офисами и договорами'),
('client', 'Арендатор, просмотр и заявки')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL
);

INSERT INTO statuses (code, group_name, name) VALUES 
('new', 'application', 'Новая заявка'),
('approved', 'application', 'Одобрено'),
('rejected', 'application', 'Отказано'),
('active', 'contract', 'Действует'),
('expired', 'contract', 'Истек'),
('free', 'office', 'Свободен'),
('rented', 'office', 'Сдан')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    full_name VARCHAR(100),
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
VALUES 
('admin', crypt('admin123', gen_salt('bf', 12)), 'admin@business-center.ru', '+7 (999) 000-00-01', 'Админ Админов Админович', 1, TRUE),
('manager', crypt('manager123', gen_salt('bf', 12)), 'a.smirnova@business-center.ru', '+7 (999) 000-00-02', 'Менеджер Менеджеров Менеджерович', 2, TRUE),
('client', crypt('client123', gen_salt('bf', 12)), 'ivan.tech@gmail.com', '+7 (900) 121-52-13', 'Клиент Клиентов Клиентович', 3, TRUE)
ON CONFLICT (login) DO NOTHING;

CREATE TABLE IF NOT EXISTS offices (
    id SERIAL PRIMARY KEY,
    office_number VARCHAR(20) NOT NULL,
    floor INT NOT NULL,
    area_sqm NUMERIC(10, 2) NOT NULL,
    price_per_month NUMERIC(12, 2) NOT NULL,
    description TEXT,
    amenities JSONB,
    is_free BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO offices (office_number, floor, area_sqm, price_per_month, description, amenities, is_free) VALUES
('101', 1, 150.00, 45000.00, 'Просторное помещение на первом этаже. Под склад или архив.', '{"wifi": true, "parking": true}', TRUE),
('102', 1, 120.50, 38000.00, 'Офис с отдельным входом. Удобно для курьерской службы.', '{"wifi": true, "kitchen": true}', TRUE),
('103', 1, 85.00, 29000.00, 'Небольшой офис в зоне ресепшн.', '{"wifi": true}', FALSE),
('201', 2, 45.00, 22000.00, 'Светлый офис с видом во двор.', '{"wifi": true, "elevator": true}', TRUE),
('202', 2, 45.00, 22000.00, 'Аналогичный офис рядом.', '{"wifi": true}', FALSE),
('203', 2, 60.00, 28000.00, 'Угловой офис с двумя окнами.', '{"wifi": true, "conditioning": true}', TRUE),
('204', 2, 30.00, 15000.00, 'Кабинет для одного-двух сотрудников.', '{"wifi": true}', TRUE),
('205', 2, 100.00, 45000.00, 'Переговорная зона + 2 кабинета.', '{"meeting_room": true}', FALSE),
('301', 3, 55.00, 32000.00, 'Офис с дизайнерским ремонтом.', '{"premium": true}', TRUE),
('302', 3, 55.00, 32000.00, 'Зеркальный офис напротив.', '{"premium": true}', TRUE),
('303', 3, 80.00, 42000.00, 'Просторный офис для IT-команды.', '{"server_room": true}', FALSE),
('304', 3, 40.00, 24000.00, 'Тихий офис в конце коридора.', '{"conditioning": true}', TRUE),
('305', 3, 120.00, 60000.00, 'Целый блок из 3 комнат.', '{"meeting_room": true, "premium": true}', TRUE),
('401', 4, 50.00, 30000.00, 'Панорамные окна, вид на город.', '{"view": true}', TRUE),
('402', 4, 50.00, 30000.00, 'Аналогичный видовой офис.', '{"view": true}', FALSE),
('403', 4, 75.00, 40000.00, 'Большой зал + кабинет руководителя.', '{"boss_room": true, "view": true}', TRUE),
('404', 4, 35.00, 21000.00, 'Компактный офис.', '{"elevator": true}', TRUE),
('405', 4, 90.00, 48000.00, 'Офис с зоной отдыха.', '{"lounge": true}', FALSE),
('501', 5, 200.00, 120000.00, 'Премиальный этаж. Терраса, большая зона кухни и отдыха.', '{"terrace": true, "kitchen_premium": true, "premium": true}', TRUE),
('502', 5, 150.00, 95000.00, 'Вторая часть премиального этажа.', '{"terrace": true, "premium": true}', TRUE);

CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    office_id INT NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    status_id INT NOT NULL REFERENCES statuses(id),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS contracts (
    id SERIAL PRIMARY KEY,
    application_id INT UNIQUE REFERENCES applications(id),
    user_id INT NOT NULL REFERENCES users(id),
    office_id INT NOT NULL REFERENCES offices(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_amount NUMERIC(14, 2) NOT NULL,
    status_id INT NOT NULL REFERENCES statuses(id),
    signed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO statuses (code, group_name, name) 
VALUES ('contract_created', 'application', 'Договор создан')
ON CONFLICT (code, group_name) DO NOTHING;

-- Добавить колонки для удобства
ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_number INT;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS paid_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    contract_id INT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status_id INT NOT NULL REFERENCES statuses(id),
    transaction_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS office_views (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    office_id INT NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    viewed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,
    is_contacted BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INT,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
-- Таблица избранных офисов пользователей
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    office_id INTEGER NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, office_id)
);
-- ============================================================
-- ТАБЛИЦА ДЛЯ ИЗОБРАЖЕНИЙ ОФИСОВ
-- ============================================================

CREATE TABLE IF NOT EXISTS office_images (
    id SERIAL PRIMARY KEY,
    office_id INTEGER NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для office_images
CREATE INDEX IF NOT EXISTS idx_office_images_office_id ON office_images(office_id);
CREATE INDEX IF NOT EXISTS idx_office_images_primary ON office_images(office_id, is_primary) WHERE is_primary = TRUE;
CREATE INDEX IF NOT EXISTS idx_office_images_order ON office_images(office_id, sort_order);
-- ============================================================
-- ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ ЗАПРОСОВ
-- ============================================================

-- 1. Индексы для audit_log (журнал аудита)
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON audit_log(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_composite ON audit_log(created_at, action_type, table_name);

-- 2. Индексы для office_views (просмотры офисов)
CREATE INDEX IF NOT EXISTS idx_office_views_viewed_at ON office_views(viewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_office_views_office_id ON office_views(office_id);
CREATE INDEX IF NOT EXISTS idx_office_views_user_id ON office_views(user_id);
CREATE INDEX IF NOT EXISTS idx_office_views_composite ON office_views(office_id, viewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_office_views_user_office ON office_views(user_id, office_id);

-- 3. Индексы для applications (заявки)
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_office_id ON applications(office_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status_id ON applications(status_id);
CREATE INDEX IF NOT EXISTS idx_applications_composite ON applications(status_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_office_status ON applications(office_id, status_id);

-- 4. Индексы для contracts (договоры)
CREATE INDEX IF NOT EXISTS idx_contracts_signed_at ON contracts(signed_at DESC);
CREATE INDEX IF NOT EXISTS idx_contracts_office_id ON contracts(office_id);
CREATE INDEX IF NOT EXISTS idx_contracts_user_id ON contracts(user_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status_id ON contracts(status_id);
CREATE INDEX IF NOT EXISTS idx_contracts_dates ON contracts(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_contracts_active ON contracts(office_id, status_id) WHERE status_id = 4;

-- 5. Индексы для payments (платежи)
CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date DESC);
CREATE INDEX IF NOT EXISTS idx_payments_contract_id ON payments(contract_id);
CREATE INDEX IF NOT EXISTS idx_payments_status_id ON payments(status_id);
CREATE INDEX IF NOT EXISTS idx_payments_composite ON payments(contract_id, payment_date DESC);

-- 6. Индексы для offices (офисы)
CREATE INDEX IF NOT EXISTS idx_offices_floor ON offices(floor);
CREATE INDEX IF NOT EXISTS idx_offices_is_free ON offices(is_free);
CREATE INDEX IF NOT EXISTS idx_offices_price ON offices(price_per_month);
CREATE INDEX IF NOT EXISTS idx_offices_composite ON offices(is_free, floor, price_per_month);

-- 7. Индексы для users (пользователи)
CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- 8. Частичные индексы для частых запросов
CREATE INDEX IF NOT EXISTS idx_offices_free_only ON offices(id, office_number, floor, price_per_month) WHERE is_free = TRUE;
CREATE INDEX IF NOT EXISTS idx_contracts_active_only ON contracts(office_id, user_id, end_date) WHERE status_id = 4;
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_office_id ON favorites(office_id);

-- Выполните в БД для настройки автоочистки

-- Функция для автоматической очистки старого аудита
CREATE OR REPLACE FUNCTION clean_audit_log()
RETURNS void AS $$
DECLARE
    row_count INTEGER;
    total_size BIGINT;
BEGIN
    -- 1. Получаем количество записей
    SELECT COUNT(*) INTO row_count FROM audit_log;
    
    -- 2. Получаем размер таблицы в MB
    SELECT pg_total_relation_size('audit_log') / 1024 / 1024 INTO total_size;
    
    -- 3. Если больше 100 000 записей или 200MB - удаляем старые
    IF row_count > 100000 OR total_size > 200 THEN
        -- Удаляем записи старше 90 дней (оставляем только свежие)
        DELETE FROM audit_log 
        WHERE created_at < NOW() - INTERVAL '90 days';
        
        -- Если всё ещё много - оставляем только 50 000 последних
        GET DIAGNOSTICS row_count = ROW_COUNT;
        IF row_count > 50000 THEN
            DELETE FROM audit_log 
            WHERE id NOT IN (
                SELECT id FROM audit_log 
                ORDER BY created_at DESC 
                LIMIT 50000
            );
        END IF;
        
        RAISE NOTICE 'Audit log cleaned: removed %, now size is % records', 
                     row_count, (SELECT COUNT(*) FROM audit_log);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Запускаем очистку каждый день в 3:00 (через pg_cron или внешний планировщик)
-- Если pg_cron установлен:
-- SELECT cron.schedule('clean-audit', '0 3 * * *', 'SELECT clean_audit_log();');