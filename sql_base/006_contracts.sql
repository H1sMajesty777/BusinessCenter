CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    application_id INT UNIQUE REFERENCES applications(id), -- Связь 1 к 1 с заявкой
    user_id INT NOT NULL REFERENCES users(id),
    office_id INT NOT NULL REFERENCES offices(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_amount NUMERIC(14, 2) NOT NULL,
    status_id INT NOT NULL REFERENCES statuses(id),
    signed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contracts_dates ON contracts(start_date, end_date);