-- Эта таблица собирает данные для обучения нейросети
CREATE TABLE office_views (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL, -- Если юзер удалится, история останется
    office_id INT NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
    viewed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT, -- Сколько времени смотрел карточку офиса
    is_contacted BOOLEAN DEFAULT FALSE -- Нажал ли кнопку "Связаться"
);

CREATE INDEX idx_views_office ON office_views(office_id);
CREATE INDEX idx_views_time ON office_views(viewed_at);