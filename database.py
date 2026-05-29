"""
資料庫操作層 — 所有 SQLite 讀寫集中於此模組
"""
import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化資料庫，建立所有資料表"""
    with get_connection() as conn:
        conn.executescript("""
        -- 交易記錄表
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,
            broker      TEXT    NOT NULL,
            symbol      TEXT    NOT NULL,
            action      TEXT    NOT NULL CHECK(action IN ('BUY','SELL')),
            shares      REAL    NOT NULL CHECK(shares > 0),
            price       REAL    NOT NULL CHECK(price > 0),
            fee         REAL    DEFAULT 0,
            note        TEXT    DEFAULT ''
        );

        -- 配股配息事件表
        CREATE TABLE IF NOT EXISTS dividend_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol          TEXT    NOT NULL,
            ex_date         TEXT,
            pay_date        TEXT,
            type            TEXT    NOT NULL CHECK(type IN ('CASH','STOCK')),
            cash_amount     REAL    DEFAULT 0,
            stock_ratio     REAL    DEFAULT 0,
            is_applied      INTEGER DEFAULT 0,
            source          TEXT    DEFAULT 'manual',
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        -- 觀察清單 / 提醒設定表
        CREATE TABLE IF NOT EXISTS watchlist (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol          TEXT    NOT NULL UNIQUE,
            target_price    REAL,
            ma60_alert      INTEGER DEFAULT 0,
            yield_threshold REAL,
            alert_enabled   INTEGER DEFAULT 1,
            last_alerted    TEXT,
            note            TEXT    DEFAULT ''
        );

        -- 股價快取表
        CREATE TABLE IF NOT EXISTS price_cache (
            symbol      TEXT    PRIMARY KEY,
            price       REAL,
            change_pct  REAL,
            volume      REAL,
            updated_at  TEXT
        );

        -- 通知設定表
        CREATE TABLE IF NOT EXISTS notification_settings (
            key     TEXT PRIMARY KEY,
            value   TEXT
        );
        """)
        conn.commit()


# ══════════════════════════════════════════════════════════════
#  交易記錄 CRUD
# ══════════════════════════════════════════════════════════════

def add_transaction(date: str, broker: str, symbol: str, action: str,
                    shares: float, price: float, fee: float = 0, note: str = "") -> int:
    """新增交易記錄，回傳新記錄的 id"""
    symbol = symbol.upper().strip()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO transactions (date, broker, symbol, action, shares, price, fee, note)
               VALUES (?,?,?,?,?,?,?,?)""",
            (date, broker, symbol, action, shares, price, fee, note)
        )
        conn.commit()
        return cur.lastrowid


def delete_transaction(txn_id: int):
    """刪除指定交易記錄"""
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        conn.commit()


def get_all_transactions() -> pd.DataFrame:
    """取得所有交易記錄"""
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM transactions ORDER BY date DESC, id DESC", conn
        )
    return df


def import_transactions_from_csv(df: pd.DataFrame) -> int:
    """從 DataFrame 批次匯入交易記錄，回傳匯入筆數"""
    required_cols = {"date", "broker", "symbol", "action", "shares", "price"}
    df.columns = [c.lower().strip() for c in df.columns]
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV 缺少必要欄位: {required_cols - set(df.columns)}")

    df["symbol"] = df["symbol"].str.upper().str.strip()
    df["action"] = df["action"].str.upper().str.strip()
    df["fee"]    = df.get("fee", 0).fillna(0)
    df["note"]   = df.get("note", "").fillna("")

    count = 0
    with get_connection() as conn:
        for _, row in df.iterrows():
            conn.execute(
                """INSERT INTO transactions (date, broker, symbol, action, shares, price, fee, note)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (str(row["date"]), row["broker"], row["symbol"], row["action"],
                 float(row["shares"]), float(row["price"]),
                 float(row["fee"]), str(row["note"]))
            )
            count += 1
        conn.commit()
    return count


# ══════════════════════════════════════════════════════════════
#  配股配息 CRUD
# ══════════════════════════════════════════════════════════════

def add_dividend_event(symbol: str, ex_date: str, pay_date: str, dtype: str,
                       cash_amount: float = 0, stock_ratio: float = 0,
                       source: str = "manual") -> int:
    symbol = symbol.upper().strip()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO dividend_events
               (symbol, ex_date, pay_date, type, cash_amount, stock_ratio, source)
               VALUES (?,?,?,?,?,?,?)""",
            (symbol, ex_date, pay_date, dtype, cash_amount, stock_ratio, source)
        )
        conn.commit()
        return cur.lastrowid


def get_dividend_events(symbol: str = None) -> pd.DataFrame:
    sql = "SELECT * FROM dividend_events ORDER BY ex_date DESC"
    params = ()
    if symbol:
        sql = "SELECT * FROM dividend_events WHERE symbol=? ORDER BY ex_date DESC"
        params = (symbol.upper(),)
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def mark_dividend_applied(div_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE dividend_events SET is_applied=1 WHERE id=?", (div_id,))
        conn.commit()


def delete_dividend_event(div_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM dividend_events WHERE id=?", (div_id,))
        conn.commit()


def upsert_dividend_events_bulk(rows: list[dict]):
    """批次寫入配息事件（來自自動抓取），避免重複"""
    with get_connection() as conn:
        for r in rows:
            conn.execute(
                """INSERT OR IGNORE INTO dividend_events
                   (symbol, ex_date, pay_date, type, cash_amount, stock_ratio, source)
                   VALUES (?,?,?,?,?,?,?)""",
                (r["symbol"], r.get("ex_date",""), r.get("pay_date",""),
                 r["type"], r.get("cash_amount",0), r.get("stock_ratio",0), "auto")
            )
        conn.commit()


# ══════════════════════════════════════════════════════════════
#  觀察清單 CRUD
# ══════════════════════════════════════════════════════════════

def get_watchlist() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM watchlist ORDER BY symbol", conn)


def upsert_watchlist(symbol: str, target_price=None, ma60_alert=0,
                     yield_threshold=None, alert_enabled=1, note=""):
    symbol = symbol.upper().strip()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO watchlist (symbol, target_price, ma60_alert, yield_threshold, alert_enabled, note)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(symbol) DO UPDATE SET
                   target_price=excluded.target_price,
                   ma60_alert=excluded.ma60_alert,
                   yield_threshold=excluded.yield_threshold,
                   alert_enabled=excluded.alert_enabled,
                   note=excluded.note""",
            (symbol, target_price, ma60_alert, yield_threshold, alert_enabled, note)
        )
        conn.commit()


def delete_watchlist(symbol: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM watchlist WHERE symbol=?", (symbol.upper(),))
        conn.commit()


def update_last_alerted(symbol: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE watchlist SET last_alerted=? WHERE symbol=?",
            (datetime.now().isoformat(), symbol.upper())
        )
        conn.commit()


# ══════════════════════════════════════════════════════════════
#  股價快取
# ══════════════════════════════════════════════════════════════

def upsert_price_cache(symbol: str, price: float, change_pct: float, volume: float = 0):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO price_cache (symbol, price, change_pct, volume, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(symbol) DO UPDATE SET
                   price=excluded.price,
                   change_pct=excluded.change_pct,
                   volume=excluded.volume,
                   updated_at=excluded.updated_at""",
            (symbol.upper(), price, change_pct, volume, datetime.now().isoformat())
        )
        conn.commit()


def get_price_cache() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM price_cache", conn)


# ══════════════════════════════════════════════════════════════
#  通知設定
# ══════════════════════════════════════════════════════════════

def save_notification_settings(telegram_token: str, telegram_chat_id: str, line_token: str):
    with get_connection() as conn:
        for key, val in [("telegram_token", telegram_token),
                         ("telegram_chat_id", telegram_chat_id),
                         ("line_token", line_token)]:
            conn.execute(
                "INSERT OR REPLACE INTO notification_settings (key, value) VALUES (?,?)",
                (key, val)
            )
        conn.commit()


def load_notification_settings() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM notification_settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


# ══════════════════════════════════════════════════════════════
#  工具函數
# ══════════════════════════════════════════════════════════════

def get_portfolio_symbols() -> list[str]:
    """取得目前有庫存的股票代號清單"""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT symbol FROM transactions GROUP BY symbol
               HAVING SUM(CASE action WHEN 'BUY' THEN shares ELSE -shares END) > 0.01"""
        ).fetchall()
    return [r["symbol"] for r in rows]


def seed_test_data():
    """插入測試用範例數據（只在資料庫是空的時候執行）"""
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    if count > 0:
        return

    test_transactions = [
        ("2024-01-15", "TCBS", "FPT", "BUY",  1000, 115000, 115000 * 0.0015),
        ("2024-03-10", "TCBS", "FPT", "BUY",   500, 108000, 108000 * 500 * 0.0015),
        ("2024-02-20", "PHS",  "TCB", "BUY",  2000,  25000,  25000 * 2000 * 0.0015),
        ("2024-04-05", "PHS",  "HPG", "BUY",  3000,  27500,  27500 * 3000 * 0.0015),
        ("2024-05-01", "TCBS", "VEA", "BUY",  1500,  34000,  34000 * 1500 * 0.0015),
        ("2024-06-15", "TCBS", "FPT", "SELL",  200, 125000, 125000 * 200 * 0.0015),
        ("2024-08-20", "PHS",  "TCB", "BUY",  1000,  22000,  22000 * 1000 * 0.0015),
    ]
    for t in test_transactions:
        add_transaction(*t)

    # 測試配息事件
    test_dividends = [
        ("FPT", "2024-06-10", "2024-07-05", "CASH", 3000, 0),
        ("FPT", "2024-06-10", "2024-07-20", "STOCK", 0, 0.10),
        ("TCB", "2024-03-20", "2024-04-15", "CASH", 1500, 0),
        ("HPG", "2024-05-15", "2024-06-10", "STOCK", 0, 0.15),
        ("VEA", "2024-07-01", "2024-08-01", "CASH", 5000, 0),
    ]
    for d in test_dividends:
        add_dividend_event(*d)

    # 測試觀察清單
    test_watchlist = [
        ("FPT",  110000, 1, 0.05),
        ("MWG",   35000, 0, 0.06),
        ("VNM",   58000, 1, 0.07),
    ]
    for w in test_watchlist:
        upsert_watchlist(w[0], w[1], w[2], w[3])


# 初始化
init_db()
