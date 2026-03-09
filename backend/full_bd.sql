
-- 001 roles
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

INSERT INTO roles (name, description) VALUES 
('admin', 'Полный доступ к системе'),
('manager', 'Управление офисами и договорами'),
('client', 'Арендатор, просмотр и заявки');

-- 002 statuses
CREATE TABLE statuses (
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
('rented', 'office', 'Сдан');

-- 003 users
CREATE TABLE users (
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
CREATE INDEX idx_users_role ON users(role_id);

INSERT INTO users (login, password_hash, email, full_name, role_id, is_active)
VALUES 
('admin', 'admin123', 'admin@office.ru', 'Админ', 1, TRUE),
('manager', 'man123', 'man@office.ru', 'Менеджер', 2, TRUE),
('client', 'cli123', 'cli@office.ru', 'Клиент', 3, TRUE);

-- 004 offices
CREATE TABLE offices (
    id SERIAL PRIMARY KEY,
    office_number VARCHAR(20) NOT NULL,
    floor INT NOT NULL,
    area_sqm NUMERIC(10, 2) NOT NULL,
    price_per_month NUMERIC(12, 2) NOT NULL,
    description TEXT,
    amenities JSONB,
    status_id INT NOT NULL REFERENCES statuses(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO offices (office_number, floor, area_sqm, price_per_month, description, amenities, status_id) VALUES 
-- Этаж 1
('101', 1, 150.00, 45000.00, 'Просторное помещение на первом этаже. Под склад или архив.', '{"wifi": true, "parking": true, "elevator": false, "security": true}', 6),
('102', 1, 120.50, 38000.00, 'Офис с отдельным входом. Удобно для курьерской службы.', '{"wifi": true, "parking": true, "kitchen": true}', 6),
('103', 1, 85.00, 29000.00, 'Небольшой офис в зоне ресепшн.', '{"wifi": true, "security": true}', 7),

-- Этаж 2
('201', 2, 45.00, 22000.00, 'Светлый офис с видом во двор.', '{"wifi": true, "parking": true, "elevator": true, "conditioning": true}', 6),
('202', 2, 45.00, 22000.00, 'Аналогичный офис рядом.', '{"wifi": true, "elevator": true}', 7),
('203', 2, 60.00, 28000.00, 'Угловой офис с двумя окнами.', '{"wifi": true, "parking": true, "elevator": true, "conditioning": true}', 6),
('204', 2, 30.00, 15000.00, 'Кабинет для одного-двух сотрудников.', '{"wifi": true, "elevator": true, "conditioning": true}', 6),
('205', 2, 100.00, 45000.00, 'Переговорная зона + 2 кабинета.', '{"wifi": true, "parking": true, "elevator": true, "meeting_room": true}', 7),

-- Этаж 3
('301', 3, 55.00, 32000.00, 'Офис с дизайнерским ремонтом.', '{"wifi": true, "parking": true, "elevator": true, "premium": true}', 6),
('302', 3, 55.00, 32000.00, 'Зеркальный офис напротив.', '{"wifi": true, "parking": true, "elevator": true, "premium": true}', 6),
('303', 3, 80.00, 42000.00, 'Просторный офис для IT-команды.', '{"wifi": true, "parking": true, "elevator": true, "server_room": true}', 7),
('304', 3, 40.00, 24000.00, 'Тихий офис в конце коридора.', '{"wifi": true, "elevator": true, "conditioning": true}', 6),
('305', 3, 120.00, 60000.00, 'Целый блок из 3 комнат.', '{"wifi": true, "parking": true, "elevator": true, "meeting_room": true, "premium": true}', 6),

-- Этаж 4
('401', 4, 50.00, 30000.00, 'Панорамные окна, вид на город.', '{"wifi": true, "parking": true, "elevator": true, "view": true}', 6),
('402', 4, 50.00, 30000.00, 'Аналогичный видовой офис.', '{"wifi": true, "parking": true, "elevator": true, "view": true}', 7),
('403', 4, 75.00, 40000.00, 'Большой зал + кабинет руководителя.', '{"wifi": true, "parking": true, "elevator": true, "view": true, "boss_room": true}', 6),
('404', 4, 35.00, 21000.00, 'Компактный офис.', '{"wifi": true, "elevator": true}', 6),
('405', 4, 90.00, 48000.00, 'Офис с зоной отдыха.', '{"wifi": true, "parking": true, "elevator": true, "lounge": true}', 7),

-- Этаж 5
('501', 5, 200.00, 120000.00, 'Премиальный этаж. Терраса, большая зона кухни и отдыха.', '{"wifi": true, "parking": true, "elevator": true, "terrace": true, "kitchen_premium": true, "premium": true}', 6),
('502', 5, 150.00, 95000.00, 'Вторая часть премиального этажа.', '{"wifi": true, "parking": true, "elevator": true, "terrace": true, "premium": true}', 6);


CREATE INDEX idx_offices_status ON offices(status_id);
CREATE INDEX idx_offices_price ON offices(price_per_month);

-- 005 applications
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    office_id INT NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    status_id INT NOT NULL REFERENCES statuses(id),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ
);
CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status_id);

-- 006 contracts
CREATE TABLE contracts (
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
CREATE INDEX idx_contracts_dates ON contracts(start_date, end_date);

-- 007 payments
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    contract_id INT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status_id INT NOT NULL REFERENCES statuses(id),
    transaction_id VARCHAR(100)
);
CREATE INDEX idx_payments_contract ON payments(contract_id);

-- 008 ai activity
CREATE TABLE office_views (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    office_id INT NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    viewed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,
    is_contacted BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_views_office ON office_views(office_id);
CREATE INDEX idx_views_time ON office_views(viewed_at);

-- 009 audit
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INT,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);



