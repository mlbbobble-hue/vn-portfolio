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

    from supabase import create_client, ClientOptions
    import streamlit as st
    
    # Check if we have an active user session token
    # st.session_state might not be available outside Streamlit context
    access_token = None
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx():
            access_token = st.session_state.get("access_token")
    except Exception:
        pass
        
    if access_token:
        options = ClientOptions(headers={"Authorization": f"Bearer {access_token}"})
        return create_client(url, key, options=options)
    
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
        import traceback
        tb = traceback.format_exc()
        return {"success": False, "user": None, "error": f"{str(e)}\n\nTraceback: {tb}"}


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




def refresh_login(refresh_token: str) -> dict:
    """用 refresh_token 重新登入"""
    try:
        client = _get_client()
        res = client.auth.refresh_session(refresh_token)
        if res.session:
            return {"success": True, "session": res.session, "user": res.user, "error": ""}
        return {"success": False, "error": "Token expired"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in_with_google():
    """取得 Google 登入網址"""
    try:
        client = _get_client()
        res = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "query_params": {"prompt": "select_account"}
            }
        })
        return {"success": True, "url": res.url}
    except Exception as e:
        return {"success": False, "error": str(e)}

def exchange_code(code: str) -> dict:
    """用 URL 中的 code 交換 session"""
    try:
        client = _get_client()
        res = client.auth.exchange_code_for_session({"auth_code": code})
        if res.session:
            return {"success": True, "session": res.session, "user": res.user}
        return {"success": False, "error": "登入失敗"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ══════════════════════════════════════════════════════════════
#  審核機制 (Admin Approval)
# ══════════════════════════════════════════════════════════════

def sb_check_approval(user_id: str, email: str) -> dict:
    """
    檢查用戶是否通過審核。
    如果資料庫沒這筆資料，代表是新用戶，自動新增一筆並發信通知管理員。
    回傳: {"is_approved": bool, "is_admin": bool, "is_new": bool}
    """
    try:
        client = _get_client()
        res = client.table("users_approval").select("*").eq("user_id", user_id).execute()
        data = res.data
        if not data:
            # 新用戶，自動新增
            client.table("users_approval").insert({
                "user_id": user_id,
                "email": email,
                "is_approved": False,
                "is_admin": False
            }).execute()
            return {"is_approved": False, "is_admin": False, "is_new": True}
        
        return {
            "is_approved": data[0].get("is_approved", False),
            "is_admin": data[0].get("is_admin", False),
            "is_new": False
        }
    except Exception as e:
        # 如果發生錯誤 (可能表單還沒建)，為了不要卡死，暫時回傳 false
        return {"is_approved": False, "is_admin": False, "is_new": False, "error": str(e)}

def sb_get_all_users_approval(admin_id: str):
    """取得所有用戶的審核狀態 (限管理員)"""
    res = _table("users_approval").select("*").order("created_at", desc=True).execute()
    import pandas as pd
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def sb_update_user_approval(admin_id: str, target_user_id: str, is_approved: bool):
    """管理員更新用戶審核狀態"""
    _table("users_approval").update({"is_approved": is_approved}).eq("user_id", target_user_id).execute()


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


def sb_update_transaction(user_id: str, txn_id: int, updates: dict):
    _table("transactions").update(updates).eq("id", txn_id).eq("user_id", user_id).execute()


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
    """取得有庫存的股票代號（排除債券，因為債券不參與自動報價更新）"""
    res = _table("transactions").select("symbol,action,shares,note")\
          .eq("user_id", user_id).execute()
    if not res.data:
        return []
    holdings: dict[str, float] = {}
    bond_symbols: set = set()
    for row in res.data:
        sym  = row["symbol"]
        s    = float(row["shares"])
        act  = row["action"]
        note = row.get("note", "") or ""
        holdings[sym] = holdings.get(sym, 0) + (s if act == "BUY" else -s)
        if "[BOND]" in note.upper():
            bond_symbols.add(sym)
    # 回傳有庫存且非債券的股票
    return [s for s, cnt in holdings.items() if cnt > 0.01 and s not in bond_symbols]
