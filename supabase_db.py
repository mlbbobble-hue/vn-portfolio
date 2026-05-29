"""
supabase_db.py — Supabase PostgreSQL 資料庫操作層
生產環境（雲端）使用此模組；本機開發仍使用 database.py（SQLite）
"""
import os
import pandas as pd
from datetime import datetime


def _get_client():
    """取得 Supabase 客戶端"""
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or os.getenv("SUPABASE_KEY", "")
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        raise RuntimeError("未設定 SUPABASE_URL 或 SUPABASE_KEY")

    from supabase import create_client
    return create_client(url, key)


def is_supabase_available() -> bool:
    """檢查 Supabase 環境是否可用"""
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "")
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
    return bool(url)


# ══════════════════════════════════════════════════════════════
#  Supabase Auth 操作
# ══════════════════════════════════════════════════════════════

def sign_up(email: str, password: str, full_name: str = "") -> dict:
    """
    用戶註冊
    回傳: {"success": bool, "user": ..., "error": str}
    """
    try:
        client = _get_client()
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}}
        })
        if res.user:
            return {"success": True, "user": res.user, "error": ""}
        return {"success": False, "user": None, "error": "未知錯誤"}
    except Exception as e:
        return {"success": False, "user": None, "error": str(e)}


def sign_in(email: str, password: str) -> dict:
    """
    用戶登入
    回傳: {"success": bool, "session": ..., "user": ..., "error": str}
    """
    try:
        client = _get_client()
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            return {"success": True, "session": res.session,
                    "user": res.user, "error": ""}
        return {"success": False, "session": None, "user": None, "error": "登入失敗"}
    except Exception as e:
        err = str(e)
        if "Invalid login credentials" in err:
            err = "Email 或密碼錯誤"
        elif "Email not confirmed" in err:
            err = "EMAIL_NOT_CONFIRMED"
        return {"success": False, "session": None, "user": None, "error": err}


def sign_out():
    """登出"""
    try:
        _get_client().auth.sign_out()
    except Exception:
        pass


def get_user_from_token(access_token: str) -> dict | None:
    """用 access token 驗證並取得用戶資訊"""
    try:
        client = _get_client()
        res = client.auth.get_user(access_token)
        if res.user:
            return {"id": res.user.id, "email": res.user.email,
                    "full_name": (res.user.user_metadata or {}).get("full_name", "")}
    except Exception:
        pass
    return None


def reset_password(email: str) -> bool:
    """發送重設密碼 Email"""
    try:
        _get_client().auth.reset_password_email(email)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════
#  工具：帶 user_id 的查詢輔助
# ══════════════════════════════════════════════════════════════

def _table(name: str):
    return _get_client().table(name)


def _to_df(response) -> pd.DataFrame:
    data = response.data or []
    return pd.DataFrame(data) if data else pd.DataFrame()


# ══════════════════════════════════════════════════════════════
#  交易記錄 CRUD（Supabase）
# ══════════════════════════════════════════════════════════════

def sb_add_transaction(user_id: str, date: str, broker: str, symbol: str,
                       action: str, shares: float, price: float,
                       fee: float = 0, note: str = "") -> int | None:
    try:
        res = _table("transactions").insert({
            "user_id": user_id, "date": date, "broker": broker,
            "symbol": symbol.upper(), "action": action,
            "shares": shares, "price": price, "fee": fee, "note": note,
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        raise RuntimeError(f"Supabase insert transaction: {e}")


def sb_delete_transaction(user_id: str, txn_id: int):
    _table("transactions").delete().eq("id", txn_id).eq("user_id", user_id).execute()


def sb_get_all_transactions(user_id: str) -> pd.DataFrame:
    res = _table("transactions").select("*").eq("user_id", user_id)\
          .order("date", desc=True).order("id", desc=True).execute()
    return _to_df(res)


def sb_import_transactions(user_id: str, df: pd.DataFrame) -> int:
    required = {"date", "broker", "symbol", "action", "shares", "price"}
    df.columns = [c.lower().strip() for c in df.columns]
    if not required.issubset(df.columns):
        raise ValueError(f"CSV 缺少欄位: {required - set(df.columns)}")
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "user_id": user_id, "date": str(row["date"]),
            "broker": row["broker"], "symbol": str(row["symbol"]).upper(),
            "action": str(row["action"]).upper(),
            "shares": float(row["shares"]), "price": float(row["price"]),
            "fee": float(row.get("fee", 0) or 0),
            "note": str(row.get("note", "") or ""),
        })
    _table("transactions").insert(rows).execute()
    return len(rows)


# ══════════════════════════════════════════════════════════════
#  配息事件 CRUD（Supabase）
# ══════════════════════════════════════════════════════════════

def sb_add_dividend_event(user_id: str, symbol: str, ex_date: str, pay_date: str,
                          dtype: str, cash_amount: float = 0,
                          stock_ratio: float = 0, source: str = "manual") -> int | None:
    res = _table("dividend_events").insert({
        "user_id": user_id, "symbol": symbol.upper(),
        "ex_date": ex_date, "pay_date": pay_date,
        "type": dtype, "cash_amount": cash_amount,
        "stock_ratio": stock_ratio, "source": source,
    }).execute()
    return res.data[0]["id"] if res.data else None


def sb_get_dividend_events(user_id: str, symbol: str = None) -> pd.DataFrame:
    q = _table("dividend_events").select("*").eq("user_id", user_id)
    if symbol:
        q = q.eq("symbol", symbol.upper())
    return _to_df(q.order("ex_date", desc=True).execute())


def sb_mark_dividend_applied(user_id: str, div_id: int):
    _table("dividend_events").update({"is_applied": True})\
      .eq("id", div_id).eq("user_id", user_id).execute()


def sb_delete_dividend_event(user_id: str, div_id: int):
    _table("dividend_events").delete().eq("id", div_id).eq("user_id", user_id).execute()


def sb_upsert_dividend_events_bulk(user_id: str, rows: list[dict]):
    inserts = []
    for r in rows:
        inserts.append({
            "user_id": user_id, "symbol": r["symbol"],
            "ex_date": r.get("ex_date", ""), "pay_date": r.get("pay_date", ""),
            "type": r["type"], "cash_amount": r.get("cash_amount", 0),
            "stock_ratio": r.get("stock_ratio", 0), "source": "auto",
        })
    if inserts:
        # upsert — 利用 ignore_duplicates 避免重複（需要在 Supabase 設定 unique constraint）
        _table("dividend_events").upsert(inserts, ignore_duplicates=True).execute()


# ══════════════════════════════════════════════════════════════
#  觀察清單（Supabase）
# ══════════════════════════════════════════════════════════════

def sb_get_watchlist(user_id: str) -> pd.DataFrame:
    res = _table("watchlist").select("*").eq("user_id", user_id)\
          .order("symbol").execute()
    return _to_df(res)


def sb_upsert_watchlist(user_id: str, symbol: str, target_price=None,
                        ma60_alert=0, yield_threshold=None,
                        alert_enabled=1, note=""):
    _table("watchlist").upsert({
        "user_id": user_id, "symbol": symbol.upper(),
        "target_price": target_price, "ma60_alert": bool(ma60_alert),
        "yield_threshold": yield_threshold,
        "alert_enabled": bool(alert_enabled), "note": note,
    }, on_conflict="user_id,symbol").execute()


def sb_delete_watchlist(user_id: str, symbol: str):
    _table("watchlist").delete().eq("user_id", user_id)\
      .eq("symbol", symbol.upper()).execute()


def sb_update_last_alerted(user_id: str, symbol: str):
    _table("watchlist").update({"last_alerted": datetime.now().isoformat()})\
      .eq("user_id", user_id).eq("symbol", symbol.upper()).execute()


# ══════════════════════════════════════════════════════════════
#  股價快取（全域，不隔離用戶）
# ══════════════════════════════════════════════════════════════

def sb_upsert_price_cache(symbol: str, price: float, change_pct: float, volume: float = 0):
    _table("price_cache").upsert({
        "symbol": symbol.upper(), "price": price,
        "change_pct": change_pct, "volume": volume,
        "updated_at": datetime.now().isoformat(),
    }, on_conflict="symbol").execute()


def sb_get_price_cache() -> pd.DataFrame:
    return _to_df(_table("price_cache").select("*").execute())


# ══════════════════════════════════════════════════════════════
#  通知設定（Supabase）
# ══════════════════════════════════════════════════════════════

def sb_save_notification_settings(user_id: str, telegram_token: str,
                                   telegram_chat_id: str, line_token: str):
    for key, val in [("telegram_token", telegram_token),
                     ("telegram_chat_id", telegram_chat_id),
                     ("line_token", line_token)]:
        _table("notification_settings").upsert({
            "user_id": user_id, "key": key, "value": val
        }, on_conflict="user_id,key").execute()


def sb_load_notification_settings(user_id: str) -> dict:
    res = _table("notification_settings").select("key,value")\
          .eq("user_id", user_id).execute()
    return {r["key"]: r["value"] for r in (res.data or [])}


# ══════════════════════════════════════════════════════════════
#  持倉符號查詢
# ══════════════════════════════════════════════════════════════

def sb_get_portfolio_symbols(user_id: str) -> list[str]:
    """取得有庫存的股票代號（使用 SQL RPC 或客戶端計算）"""
    res = _table("transactions").select("symbol,action,shares")\
          .eq("user_id", user_id).execute()
    if not res.data:
        return []
    holdings: dict[str, float] = {}
    for row in res.data:
        sym  = row["symbol"]
        s    = float(row["shares"])
        act  = row["action"]
        holdings[sym] = holdings.get(sym, 0) + (s if act == "BUY" else -s)
    return [s for s, cnt in holdings.items() if cnt > 0.01]
