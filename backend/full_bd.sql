CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 001 ROLES
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

-- 002 STATUSES
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

-- 003 USERS (с хешированными паролями!)
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
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);

INSERT INTO users (login, password_hash, email, phone, full_name, role_id, is_active)
VALUES 
('admin', crypt('admin123', gen_salt('bf', 12)), 'admin@business-center.ru', '+7 (999) 000-00-01', 'Админ Админов Админович', 1, TRUE),
('manager', crypt('manager123', gen_salt('bf', 12)), 'a.smirnova@business-center.ru', '+7 (999) 000-00-02', 'Менеджер Менеджеров Менеджерович', 2, TRUE),
('client', crypt('client123', gen_salt('bf', 12)), 'ivan.tech@gmail.com', '+7 (900) 121-52-13', 'Клиент Клиентов Клиентович', 3, TRUE)
ON CONFLICT (login) DO NOTHING;

-- 004 OFFICES
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
CREATE INDEX IF NOT EXISTS idx_offices_is_free ON offices(is_free);
CREATE INDEX IF NOT EXISTS idx_offices_price ON offices(price_per_month);

-- Заполнение офисов 
-- TRUE = Свободен, FALSE = Занят
INSERT INTO offices (office_number, floor, area_sqm, price_per_month, description, amenities, is_free) VALUES
-- Этаж 1
('101', 1, 150.00, 45000.00, 'Просторное помещение на первом этаже. Под склад или архив.', '{"wifi": true, "parking": true, "security": true}', TRUE),
('102', 1, 120.50, 38000.00, 'Офис с отдельным входом. Удобно для курьерской службы.', '{"wifi": true, "parking": true, "kitchen": true}', TRUE),
('103', 1, 85.00, 29000.00, 'Небольшой офис в зоне ресепшн.', '{"wifi": true, "security": true}', FALSE), -- Занят
-- Этаж 2
('201', 2, 45.00, 22000.00, 'Светлый офис с видом во двор.', '{"wifi": true, "parking": true, "elevator": true, "conditioning": true}', TRUE),
('202', 2, 45.00, 22000.00, 'Аналогичный офис рядом.', '{"wifi": true, "elevator": true}', FALSE), -- Занят
('203', 2, 60.00, 28000.00, 'Угловой офис с двумя окнами.', '{"wifi": true, "parking": true, "elevator": true, "conditioning": true}', TRUE),
('204', 2, 30.00, 15000.00, 'Кабинет для одного-двух сотрудников.', '{"wifi": true, "elevator": true, "conditioning": true}', TRUE),
('205', 2, 100.00, 45000.00, 'Переговорная зона + 2 кабинета.', '{"wifi": true, "parking": true, "elevator": true, "meeting_room": true}', FALSE), -- Занят
-- Этаж 3
('301', 3, 55.00, 32000.00, 'Офис с дизайнерским ремонтом.', '{"wifi": true, "parking": true, "elevator": true, "premium": true}', TRUE),
('302', 3, 55.00, 32000.00, 'Зеркальный офис напротив.', '{"wifi": true, "parking": true, "elevator": true, "premium": true}', TRUE),
('303', 3, 80.00, 42000.00, 'Просторный офис для IT-команды.', '{"wifi": true, "parking": true, "elevator": true, "server_room": true}', FALSE), -- Занят
('304', 3, 40.00, 24000.00, 'Тихий офис в конце коридора.', '{"wifi": true, "elevator": true, "conditioning": true}', TRUE),
('305', 3, 120.00, 60000.00, 'Целый блок из 3 комнат.', '{"wifi": true, "parking": true, "elevator": true, "meeting_room": true, "premium": true}', TRUE),
-- Этаж 4
('401', 4, 50.00, 30000.00, 'Панорамные окна, вид на город.', '{"wifi": true, "parking": true, "elevator": true, "view": true}', TRUE),
('402', 4, 50.00, 30000.00, 'Аналогичный видовой офис.', '{"wifi": true, "parking": true, "elevator": true, "view": true}', FALSE), -- Занят
('403', 4, 75.00, 40000.00, 'Большой зал + кабинет руководителя.', '{"wifi": true, "parking": true, "elevator": true, "view": true, "boss_room": true}', TRUE),
('404', 4, 35.00, 21000.00, 'Компактный офис.', '{"wifi": true, "elevator": true}', TRUE),
('405', 4, 90.00, 48000.00, 'Офис с зоной отдыха.', '{"wifi": true, "parking": true, "elevator": true, "lounge": true}', FALSE), -- Занят
-- Этаж 5
('501', 5, 200.00, 120000.00, 'Премиальный этаж. Терраса, большая зона кухни и отдыха.', '{"wifi": true, "parking": true, "elevator": true, "terrace": true, "kitchen_premium": true, "premium": true}', TRUE),
('502', 5, 150.00, 95000.00, 'Вторая часть премиального этажа.', '{"wifi": true, "parking": true, "elevator": true, "terrace": true, "premium": true}', TRUE);
-- 005 APPLICATIONS
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    office_id INT NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    status_id INT NOT NULL REFERENCES statuses(id),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status_id);

-- 006 CONTRACTS
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
CREATE INDEX IF NOT EXISTS idx_contracts_dates ON contracts(start_date, end_date);

-- 007 PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    contract_id INT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status_id INT NOT NULL REFERENCES statuses(id),
    transaction_id VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS idx_payments_contract ON payments(contract_id);

-- 008 OFFICE VIEWS
CREATE TABLE IF NOT EXISTS office_views (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    office_id INT NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    viewed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,
    is_contacted BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_views_office ON office_views(office_id);
CREATE INDEX IF NOT EXISTS idx_views_time ON office_views(viewed_at);

-- 009 AUDIT LOG
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