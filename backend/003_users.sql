CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Позже пароли само собой будут захэшированы, но пока я тебе просто таблицы показываю
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    full_name VARCHAR(100),
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_role ON users(role_id);