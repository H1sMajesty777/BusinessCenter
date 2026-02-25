CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL, -- CREATE, UPDATE, DELETE, LOGIN
    table_name VARCHAR(50) NOT NULL,
    record_id INT,
    old_values JSONB, -- Что было до изменения
    new_values JSONB, -- Что стало
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);