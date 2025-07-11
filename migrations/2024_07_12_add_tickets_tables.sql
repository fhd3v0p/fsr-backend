-- Миграция: Добавление таблиц для системы билетов
-- Дата: 2024-07-12

-- Примечание: поле is_premium уже добавлено в database.py при инициализации

-- Создаем таблицу для билетов за подписку на все каналы
CREATE TABLE IF NOT EXISTS tickets_subscription (
    user_id INTEGER PRIMARY KEY,
    is_subscribed_all BOOLEAN DEFAULT FALSE
);

-- Создаем таблицу для билетов за рефералов
CREATE TABLE IF NOT EXISTS tickets_referral (
    user_id INTEGER NOT NULL,
    referral_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, referral_id)
);

-- Создаем индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_tickets_subscription_user_id ON tickets_subscription(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_referral_user_id ON tickets_referral(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_referral_referral_id ON tickets_referral(referral_id);
