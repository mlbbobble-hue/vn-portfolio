"""
app.py — 主程式（首頁 Dashboard）
雙語 🇻🇳🇹🇼 + Supabase Auth + 響應式深色介面
"""
import streamlit as st

import base64
try:
    with open("assets/logo.png", "rb") as _f:
        logo_base64 = base64.b64encode(_f.read()).decode()
except:
    logo_base64 = ""


import base64
try:
    with open("assets/logo.png", "rb") as _f:
        logo_base64 = base64.b64encode(_f.read()).decode()
except:
    logo_base64 = ""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

from datetime import datetime, timedelta
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (seed_test_data, get_portfolio_symbols,
                        upsert_price_cache, get_watchlist)
from portfolio import compute_portfolio_with_prices
from db_router import get_price_cache
from market_data import get_multiple_prices
from alerts import check_and_fire_alerts
from config import PRICE_REFRESH_SECONDS

# ── 頁面設定 ───────────────────────────────────────────────────
st.set_page_config(
    page_title="VN Portfolio | 越南股市投資組合",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from theme import load_css
load_css()


# ── 全域樣式 ───────────────────────────────────────────────────


# ── 驗證登入 ───────────────────────────────────────────────────
if not check_auth():
    st.stop()


def fmt_vnd(v): 
    if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.2f} tỷ"
    if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M"
    return f"{v:,.0f}"

def fmt_pct(v):
    return f"{'▲' if v>0 else '▼' if v<0 else '─'} {abs(v):.2f}%"


# ── 自動更新股價邏輯 ──────────────────────────────────────────
if st_autorefresh:
    # 每 10 分鐘自動重啟頁面一次 (600,000 ms)
    # 真正的「更新股價」邏輯會在下面判斷
    count = st_autorefresh(interval=10 * 60 * 1000, key="price_autorefresh")

def auto_update_if_needed():
    try:
        now_utc = datetime.utcnow()
        now_vn = now_utc + timedelta(hours=7)
        
        from db_router import get_price_cache
        cache = get_price_cache()
        
        force_update = False
        
        from db_router import get_portfolio_symbols, get_watchlist
        symbols = get_portfolio_symbols()
        try:
            wl_df = get_watchlist()
            wl_syms = wl_df["symbol"].tolist() if not wl_df.empty else []
        except Exception:
            wl_syms = []
        all_syms = list(set(symbols + wl_syms))

        # 如果快取是空的，或者有新的股票代碼不在快取中，無條件觸發更新
        if cache.empty:
            force_update = True
        elif set(all_syms) - set(cache["symbol"].tolist()):
            force_update = True
        else:
            # 判斷是否為越南開盤時間：週一至週五，早上 9 點到下午 3 點
            is_market_open = (now_vn.weekday() < 5) and (9 <= now_vn.hour < 15)
            if is_market_open:
                last_update = pd.to_datetime(cache["updated_at"]).max()
                if last_update.tzinfo is not None:
                    last_update = last_update.tz_localize(None)
                if (now_utc - last_update).total_seconds() >= 3600:
                    force_update = True

        if force_update:
            symbols = get_portfolio_symbols()
            from db_router import get_watchlist
            try:
                wl_df = get_watchlist()
                wl_syms = wl_df["symbol"].tolist() if not wl_df.empty else []
            except Exception:
                wl_syms = []
            all_syms = list(set(symbols + wl_syms))
            if all_syms:
                from market_data import get_multiple_prices
                from i18n import t
                prices_df = get_multiple_prices(all_syms)
                for _, p in prices_df.iterrows():
                    upsert_price_cache(p["symbol"], p["price"], p["change_pct"], p.get("volume", 0))
    except Exception as e:
        pass

# 依賴 st_autorefresh 每 10 分鐘重整時，同步觸發檢查與更新
try:
    auto_update_if_needed()
except Exception:
    pass

# ── 側邊欄 ─────────────────────────────────────────────────────
with st.sidebar:
    render_lang_switcher()
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='text-align:center; padding:12px 0;'>
        <img src="data:image/png;base64,{logo_base64}"   style="width: 140px; height: 140px; border-radius: 12px; margin-bottom: 8px;">
    </div>
    """, unsafe_allow_html=True)

    if st.button(t("update_price"), icon=":material/refresh:", use_container_width=True):
        symbols = get_portfolio_symbols()
        wl_syms = []
        try:
            wl_df = get_watchlist()
            if not wl_df.empty:
                wl_syms = wl_df["symbol"].tolist()
        except Exception:
            pass
        all_syms = list(set(symbols + wl_syms))
        if all_syms:
            progress_bar = st.progress(0, text=f"🔄 正在更新 0/{len(all_syms)} 檔股票...")
            
            def update_progress(done, total):
                pct = done / total
                progress_bar.progress(pct, text=f"🔄 已完成 {done}/{total} 檔股票...")
            
            prices_df = get_multiple_prices(all_syms, _progress_callback=update_progress)
            for _, p in prices_df.iterrows():
                upsert_price_cache(p["symbol"], p["price"], p["change_pct"], p.get("volume", 0))
            progress_bar.progress(1.0, text=f"✅ 已完成更新 {len(prices_df)} 檔股票！")
            import time as _t
            _t.sleep(1)
            st.rerun()
                
    st.divider()
    render_user_info_sidebar()
    st.divider()

    # 提醒狀態
    try:
        fired = check_and_fire_alerts()
        if fired:
            st.markdown(f"""
            <div class="alert-banner">
                ⚠️ <b>{len(fired)} {t('warning')}</b>
                {"".join(f"<br>• {a['symbol']} @ {a['price']:,.0f}" for a in fired)}
            </div>""", unsafe_allow_html=True)
    except Exception:
        pass

    st.markdown(f"""
    <div style='margin-top:20px;font-size:0.72rem;
                color:#888;text-align:center;'>
        {t('disclaimer')}<br>{t('data_source')}
    </div>""", unsafe_allow_html=True)


# ── 主頁面 (Navigation) ──────────────────────────────────────────
dashboard_page = st.Page("views/00_dashboard.py", title=t("nav_dashboard"), icon=":material/space_dashboard:", url_path="dashboard")
portfolio_page = st.Page("views/01_portfolio.py", title=t("nav_portfolio"), icon=":material/business_center:")
transactions_page = st.Page("views/02_transactions.py", title=t("nav_transactions"), icon=":material/receipt_long:")
dividends_page = st.Page("views/03_dividends.py", title=t("nav_dividends"), icon=":material/paid:")
watchlist_page = st.Page("views/04_watchlist.py", title=t("nav_watchlist"), icon=":material/trending_up:")
settings_page = st.Page("views/05_settings.py", title=t("nav_settings"), icon=":material/settings:")

admin_page = st.Page("views/06_admin.py", title=t("nav_admin"), icon=":material/admin_panel_settings:")


nav_pages = [dashboard_page, portfolio_page, transactions_page, dividends_page, watchlist_page, settings_page]
if st.session_state.get("is_admin", False):
    nav_pages.insert(0, admin_page)

pg = st.navigation(nav_pages)

pg.run()
