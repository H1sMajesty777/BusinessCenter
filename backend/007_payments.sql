CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    contract_id INT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status_id INT NOT NULL REFERENCES statuses(id), -- paid, pending
    transaction_id VARCHAR(100) -- ID транзакции от платежной системы
);

CREATE INDEX idx_payments_contract ON payments(contract_id);