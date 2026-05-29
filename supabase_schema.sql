-- ============================================================
-- 越南股市投資組合系統 — Supabase PostgreSQL 建表腳本
-- 請在 Supabase Dashboard → SQL Editor 中執行此腳本
-- ============================================================

-- 1. 交易記錄表
CREATE TABLE IF NOT EXISTS transactions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date        DATE NOT NULL,
    broker      TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    action      TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
    shares      NUMERIC(12,2) NOT NULL,
    price       NUMERIC(12,2) NOT NULL,
    fee         NUMERIC(12,2) DEFAULT 0,
    note        TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 配息事件表
CREATE TABLE IF NOT EXISTS dividend_events (
    id           BIGSERIAL PRIMARY KEY,
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol       TEXT NOT NULL,
    ex_date      DATE,
    pay_date     DATE,
    type         TEXT NOT NULL CHECK (type IN ('CASH', 'STOCK')),
    cash_amount  NUMERIC(12,2) DEFAULT 0,
    stock_ratio  NUMERIC(6,4)  DEFAULT 0,
    is_applied   BOOLEAN DEFAULT FALSE,
    source       TEXT DEFAULT 'manual',
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, symbol, ex_date, type)
);

-- 3. 觀察清單表
CREATE TABLE IF NOT EXISTS watchlist (
    id               BIGSERIAL PRIMARY KEY,
    user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol           TEXT NOT NULL,
    target_price     NUMERIC(12,2),
    ma60_alert       BOOLEAN DEFAULT FALSE,
    yield_threshold  NUMERIC(5,4),
    alert_enabled    BOOLEAN DEFAULT TRUE,
    note             TEXT DEFAULT '',
    last_alerted     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, symbol)
);

-- 4. 股價快取表（全域，不隔離用戶）
CREATE TABLE IF NOT EXISTS price_cache (
    symbol      TEXT PRIMARY KEY,
    price       NUMERIC(12,2) NOT NULL,
    change_pct  NUMERIC(8,4) DEFAULT 0,
    volume      NUMERIC(16,0) DEFAULT 0,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 通知設定表
CREATE TABLE IF NOT EXISTS notification_settings (
    id         BIGSERIAL PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key        TEXT NOT NULL,
    value      TEXT DEFAULT '',
    UNIQUE (user_id, key)
);

-- ============================================================
-- Row Level Security (RLS) — 確保用戶只能看到自己的資料
-- ============================================================

-- transactions
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own transactions"
    ON transactions FOR ALL
    USING (auth.uid() = user_id);

-- dividend_events
ALTER TABLE dividend_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own dividend_events"
    ON dividend_events FOR ALL
    USING (auth.uid() = user_id);

-- watchlist
ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own watchlist"
    ON watchlist FOR ALL
    USING (auth.uid() = user_id);

-- price_cache (公開讀，允許匿名寫入)
ALTER TABLE price_cache ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read price_cache"
    ON price_cache FOR SELECT USING (true);
CREATE POLICY "Authenticated users can write price_cache"
    ON price_cache FOR ALL
    USING (auth.role() = 'authenticated');

-- notification_settings
ALTER TABLE notification_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own notification_settings"
    ON notification_settings FOR ALL
    USING (auth.uid() = user_id);

-- ============================================================
-- 索引（提升查詢效能）
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_transactions_user_symbol ON transactions(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date DESC);
CREATE INDEX IF NOT EXISTS idx_dividend_events_user_symbol ON dividend_events(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_dividend_events_ex_date ON dividend_events(ex_date DESC);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
