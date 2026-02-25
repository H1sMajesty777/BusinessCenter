CREATE TABLE offices (
    id SERIAL PRIMARY KEY,
    office_number VARCHAR(20) NOT NULL, -- Например, "305-А"
    floor INT NOT NULL,
    area_sqm NUMERIC(10, 2) NOT NULL, -- Площадь в м2
    price_per_month NUMERIC(12, 2) NOT NULL, -- Цена аренды
    description TEXT,
    amenities JSONB, -- Гибкое поле для удобств: {"wifi": true, "parking": false}
    status_id INT NOT NULL REFERENCES statuses(id), -- Статус офиса (свободен/занят)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_offices_status ON offices(status_id);
CREATE INDEX idx_offices_price ON offices(price_per_month); -- Важно для поиска и AI