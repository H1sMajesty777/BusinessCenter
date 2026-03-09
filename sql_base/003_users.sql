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