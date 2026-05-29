"""
app.py — 主程式（首頁 Dashboard）
雙語 🇻🇳🇹🇼 + Supabase Auth + 響應式深色介面
"""
import streamlit as st
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
        # 判斷是否為越南開盤時間：週一至週五，早上 9 點到下午 3 點
        if now_vn.weekday() >= 5: return
        if not (9 <= now_vn.hour < 15): return
        
        # 檢查最後更新時間
        from db_router import get_price_cache
        cache = get_price_cache()
        if cache.empty: return
        
        # 尋找最舊的更新時間 (避免只抓到剛更新完的)
        # 如果最舊的資料距離現在超過 60 分鐘，就觸發全面更新
        last_update = pd.to_datetime(cache["updated_at"]).max()
        if last_update.tzinfo is not None:
            last_update = last_update.tz_localize(None)
            
        if (now_utc - last_update).total_seconds() >= 3600:
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
                prices_df = get_multiple_prices(all_syms)
                for _, p in prices_df.iterrows():
                    upsert_price_cache(p["symbol"], p["price"], p["change_pct"], p.get("volume", 0))
    except Exception as e:
        pass

# 在背景執行自動檢查與更新
auto_update_if_needed()

# ── 側邊欄 ─────────────────────────────────────────────────────
with st.sidebar:
    render_lang_switcher()
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='text-align:center; padding:12px 0;'>
        <div style='font-size:2.5rem; color: var(--cathay-green);'><svg width="40" height="40" viewBox="0 0 24 24" fill="var(--cathay-green)" xmlns="http://www.w3.org/2000/svg">
<path d="M17 12C18.6569 12 20 10.6569 20 9C20 7.34315 18.6569 6 17 6C16.8202 6 16.6441 6.01579 16.4727 6.04618C15.8291 3.75549 13.6895 2 11.1111 2C8.53272 2 6.39308 3.75549 5.74945 6.04618C5.57811 6.01579 5.40194 6 5.22222 6C3.44263 6 2 7.34315 2 9C2 10.6569 3.44263 12 5.22222 12C5.35209 12 5.47955 11.9922 5.60421 11.977C6.07921 13.7277 7.72895 15 9.66667 15H10.5556V20C10.5556 21.1046 11.451 22 12.5556 22H13.4444C13.9967 22 14.4444 21.5523 14.4444 21V15H15.3333C17.2711 15 18.9208 13.7277 19.3958 11.977C19.5205 11.9922 19.6479 12 19.7778 12H17Z"/>
</svg></div>
        <div style='font-size:1.05rem; font-weight:700; color:var(--cathay-green);'>VN Portfolio</div>
        <div style='font-size:0.75rem; color:#888;'>多券商整合 • 配息追蹤 • 價格提醒</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(t("update_price"), icon=":material/refresh:", use_container_width=True):
        with st.spinner(t("updating")):
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
                prices_df = get_multiple_prices(all_syms)
                for _, p in prices_df.iterrows():
                    upsert_price_cache(p["symbol"], p["price"], p["change_pct"], p.get("volume", 0))
                st.success(t("updated_count", n=len(all_syms)))
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
dashboard_page = st.Page("pages/00_dashboard.py", title=t("nav_dashboard"), icon=":material/park:")
portfolio_page = st.Page("pages/01_portfolio.py", title=t("nav_portfolio"), icon=":material/business_center:")
transactions_page = st.Page("pages/02_transactions.py", title=t("nav_transactions"), icon=":material/receipt_long:")
dividends_page = st.Page("pages/03_dividends.py", title=t("nav_dividends"), icon=":material/paid:")
watchlist_page = st.Page("pages/04_watchlist.py", title=t("nav_watchlist"), icon=":material/notifications_active:")
analytics_page = st.Page("pages/05_analytics.py", title=t("nav_analytics"), icon=":material/monitoring:")

admin_page = st.Page("pages/06_admin.py", title="管理員後台", icon=":material/admin_panel_settings:")


nav_pages = [dashboard_page, portfolio_page, transactions_page, dividends_page, watchlist_page, analytics_page]
if st.session_state.get("is_admin", False):
    nav_pages.insert(0, admin_page)

pg = st.navigation(nav_pages)

pg.run()
