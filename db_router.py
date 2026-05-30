"""
db_router.py — 資料庫路由器
自動偵測環境，切換 SQLite（本機開發）或 Supabase（雲端生產）
所有 App 程式碼只需 import db_router，不需要知道底層
"""
import streamlit as st
import pandas as pd
from supabase_db import is_supabase_available


def _uid() -> str:
    """取得目前登入的 user_id"""
    return st.session_state.get("user_id", "local_dev_user")


def _use_cloud() -> bool:
    return is_supabase_available()


# ══════════════════════════════════════════════════════════════
#  交易記錄
# ══════════════════════════════════════════════════════════════

def add_transaction(date, broker, symbol, action, shares, price, fee=0, note=""):
    if _use_cloud():
        from supabase_db import sb_add_transaction
        return sb_add_transaction(_uid(), date, broker, symbol, action, shares, price, fee, note)
    else:
        from database import add_transaction as _add
        return _add(date, broker, symbol, action, shares, price, fee, note)


def delete_transaction(txn_id: int):
    if _use_cloud():
        from supabase_db import sb_delete_transaction
        sb_delete_transaction(_uid(), txn_id)
    else:
        from database import delete_transaction as _del
        _del(txn_id)


def update_transaction(txn_id: int, updates: dict):
    if _use_cloud():
        from supabase_db import sb_update_transaction
        sb_update_transaction(_uid(), txn_id, updates)
    else:
        from database import update_transaction as _upd
        _upd(txn_id, updates)


def get_all_transactions() -> pd.DataFrame:
    if _use_cloud():
        from supabase_db import sb_get_all_transactions
        return sb_get_all_transactions(_uid())
    else:
        from database import get_all_transactions as _get
        return _get()


def import_transactions_from_csv(df: pd.DataFrame) -> int:
    if _use_cloud():
        from supabase_db import sb_import_transactions
        return sb_import_transactions(_uid(), df)
    else:
        from database import import_transactions_from_csv as _imp
        return _imp(df)


# ══════════════════════════════════════════════════════════════
#  配息事件
# ══════════════════════════════════════════════════════════════

def add_dividend_event(symbol, ex_date, pay_date, dtype, cash_amount=0, stock_ratio=0, source="manual"):
    if _use_cloud():
        from supabase_db import sb_add_dividend_event
        return sb_add_dividend_event(_uid(), symbol, ex_date, pay_date, dtype, cash_amount, stock_ratio, source)
    else:
        from database import add_dividend_event as _add
        return _add(symbol, ex_date, pay_date, dtype, cash_amount, stock_ratio, source)


def get_dividend_events(symbol=None) -> pd.DataFrame:
    if _use_cloud():
        from supabase_db import sb_get_dividend_events
        return sb_get_dividend_events(_uid(), symbol)
    else:
        from database import get_dividend_events as _get
        return _get(symbol)


def mark_dividend_applied(div_id: int):
    if _use_cloud():
        from supabase_db import sb_mark_dividend_applied
        sb_mark_dividend_applied(_uid(), div_id)
    else:
        from database import mark_dividend_applied as _mark
        _mark(div_id)


def delete_dividend_event(div_id: int):
    if _use_cloud():
        from supabase_db import sb_delete_dividend_event
        sb_delete_dividend_event(_uid(), div_id)
    else:
        from database import delete_dividend_event as _del
        _del(div_id)


def upsert_dividend_events_bulk(rows: list[dict]):
    if _use_cloud():
        from supabase_db import sb_upsert_dividend_events_bulk
        sb_upsert_dividend_events_bulk(_uid(), rows)
    else:
        from database import upsert_dividend_events_bulk as _ups
        _ups(rows)


# ══════════════════════════════════════════════════════════════
#  觀察清單
# ══════════════════════════════════════════════════════════════

def get_watchlist() -> pd.DataFrame:
    if _use_cloud():
        from supabase_db import sb_get_watchlist
        return sb_get_watchlist(_uid())
    else:
        from database import get_watchlist as _get
        return _get()


def upsert_watchlist(symbol, target_price=None, ma60_alert=0, yield_threshold=None, alert_enabled=1, note=""):
    if _use_cloud():
        from supabase_db import sb_upsert_watchlist
        sb_upsert_watchlist(_uid(), symbol, target_price, ma60_alert, yield_threshold, alert_enabled, note)
    else:
        from database import upsert_watchlist as _ups
        _ups(symbol, target_price, ma60_alert, yield_threshold, alert_enabled, note)


def delete_watchlist(symbol: str):
    if _use_cloud():
        from supabase_db import sb_delete_watchlist
        sb_delete_watchlist(_uid(), symbol)
    else:
        from database import delete_watchlist as _del
        _del(symbol)


def update_last_alerted(symbol: str):
    if _use_cloud():
        from supabase_db import sb_update_last_alerted
        sb_update_last_alerted(_uid(), symbol)
    else:
        from database import update_last_alerted as _upd
        _upd(symbol)


# ══════════════════════════════════════════════════════════════
#  股價快取
# ══════════════════════════════════════════════════════════════

def upsert_price_cache(symbol, price, change_pct, volume=0):
    if _use_cloud():
        from supabase_db import sb_upsert_price_cache
        sb_upsert_price_cache(symbol, price, change_pct, volume)
    else:
        from database import upsert_price_cache as _ups
        _ups(symbol, price, change_pct, volume)


@st.cache_data(ttl=300, show_spinner=False)
def get_price_cache() -> pd.DataFrame:
    if _use_cloud():
        from supabase_db import sb_get_price_cache
        return sb_get_price_cache()
    else:
        from database import get_price_cache as _get
        return _get()


# ══════════════════════════════════════════════════════════════
#  通知設定
# ══════════════════════════════════════════════════════════════

def save_notification_settings(telegram_token, telegram_chat_id, line_token):
    if _use_cloud():
        from supabase_db import sb_save_notification_settings
        sb_save_notification_settings(_uid(), telegram_token, telegram_chat_id, line_token)
    else:
        from database import save_notification_settings as _save
        _save(telegram_token, telegram_chat_id, line_token)


def load_notification_settings() -> dict:
    if _use_cloud():
        from supabase_db import sb_load_notification_settings
        return sb_load_notification_settings(_uid())
    else:
        from database import load_notification_settings as _load
        return _load()


# ══════════════════════════════════════════════════════════════
#  工具函數
# ══════════════════════════════════════════════════════════════

def get_portfolio_symbols() -> list[str]:
    if _use_cloud():
        from supabase_db import sb_get_portfolio_symbols
        return sb_get_portfolio_symbols(_uid())
    else:
        from database import get_portfolio_symbols as _get
        return _get()


def seed_test_data():
    """只在本機模式下插入測試資料"""
    if not _use_cloud():
        from database import seed_test_data as _seed
        _seed()
