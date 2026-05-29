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


# ── 側邊欄 ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:12px 0;'>
        <div style='font-size:2.5rem'>📈</div>
        <div style='font-size:1.05rem; font-weight:700; color:#a78bfa;'>VN Portfolio</div>
        <div style='font-size:0.75rem; color:#64748b;'>{t('app_tagline')}</div>
    </div>
    """, unsafe_allow_html=True)

    render_lang_switcher()
    st.divider()
    render_user_info_sidebar()
    st.divider()

    if st.button(t("update_price"), use_container_width=True):
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
    <div style='position:fixed;bottom:20px;left:16px;right:16px;font-size:0.72rem;
                color:#475569;text-align:center;'>
        {t('disclaimer')}<br>{t('data_source')}
    </div>""", unsafe_allow_html=True)


# ── 主頁面 (Navigation) ──────────────────────────────────────────
dashboard_page = st.Page("pages/00_dashboard.py", title=t("nav_dashboard"), icon="🌳")
portfolio_page = st.Page("pages/01_portfolio.py", title=t("nav_portfolio"), icon="💼")
transactions_page = st.Page("pages/02_transactions.py", title=t("nav_transactions"), icon="📋")
dividends_page = st.Page("pages/03_dividends.py", title=t("nav_dividends"), icon="💵")
watchlist_page = st.Page("pages/04_watchlist.py", title=t("nav_watchlist"), icon="🔔")
analytics_page = st.Page("pages/05_analytics.py", title=t("nav_analytics"), icon="📈")

pg = st.navigation([
    dashboard_page,
    portfolio_page,
    transactions_page,
    dividends_page,
    watchlist_page,
    analytics_page
])
pg.run()
