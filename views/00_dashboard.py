"""
頁面0：首頁總覽 (Dashboard) - 國泰手機 App 風格
"""
from theme import load_css
load_css()
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

from i18n import t
from auth_page import check_auth, render_user_info_sidebar
from portfolio import compute_portfolio_with_prices, get_total_realized_pl, compute_received_dividends
from db_router import get_price_cache
from config import PRICE_REFRESH_SECONDS

st.markdown("""
<style>
/* 針對本頁面的微調 */
.app-title-small { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; display:block; }
.empty-state { text-align: center; padding: 40px 20px; background: var(--bg-card); border-radius: 12px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; color: var(--text-secondary); }
.empty-text { color: var(--text-secondary); font-size: 16px; margin-bottom: 24px; }
</style>
""", unsafe_allow_html=True)


if not check_auth():
    st.stop()

# 獲取資料

def format_vnd(amount: float) -> str:
    if abs(amount) >= 100_000_000:
        return f"{amount / 100_000_000:.2f} 億"
    else:
        return f"{amount:,.0f}"

col_title, col_toggle = st.columns([1, 1])
with col_title:
    pass # Title is already above
with col_toggle:
    show_in_twd = st.toggle(t("display_twd"), value=False)
    
EXCHANGE_RATE = 780

holdings = compute_portfolio_with_prices()

total_value = 0.0
total_cost = 0.0
total_unrealized = 0.0
roi_pct = 0.0

if not holdings.empty:
    total_value = holdings["market_value"].sum()
    total_cost = holdings["total_cost"].sum()
    total_unrealized = holdings["unrealized_pl"].sum()
    roi_pct = (total_unrealized / total_cost * 100) if total_cost > 0 else 0.0

is_loading_prices = not holdings.empty and total_value == 0 and total_cost > 0

if is_loading_prices:
    display_value = t("syncing_prices")
    display_unrealized = t("loading_values")
    display_roi = "🔄"
    st_autorefresh(interval=2000, limit=15, key="wait_for_prices")
else:
    if show_in_twd:
        display_val_num = total_value / EXCHANGE_RATE
        display_unreal_num = total_unrealized / EXCHANGE_RATE
        currency_label = "TWD"
    else:
        display_val_num = total_value
        display_unreal_num = total_unrealized
        currency_label = "VND"
        
    formatted_val = format_vnd(display_val_num)
    formatted_unreal = format_vnd(abs(display_unreal_num))
    
    display_value = f"{formatted_val} {currency_label}"
    display_unrealized = f"{'-' if display_unreal_num < 0 else ''}{formatted_unreal} {currency_label}"
    display_roi = f"{roi_pct:.2f}%"



# 1. 頂部總資產橫幅
    st.markdown(f'''
    <div class="cathay-app-header" style="margin: 0 0 20px 0;">
        <span class="app-title-small">{t("my_assets_overview")}</span>
        <div class="total-value">{display_value}</div>
    </div>
    ''', unsafe_allow_html=True)

    # 2. 投資績效 Badges & Cards
    st.markdown(f"<h4 style='margin-left: 8px;'>{t('invest_performance')}</h4>", unsafe_allow_html=True)
    if is_loading_prices:
        c_color = "var(--text-primary)"
        c_bg = "var(--bg-card)"
        trend = ""
        sign = ""
        amount_text = display_unrealized
        pct_text = display_roi
    else:
        if total_unrealized > 0:
            c_color = "#FF2A85"
            c_bg = "var(--bg-card)"
            trend = "▲ "
            sign = "+"
        elif total_unrealized < 0:
            c_color = "#9D4EDD"
            c_bg = "var(--bg-card)"
            trend = "▼ "
            sign = "-"
        else:
            c_color = "var(--text-primary)"
            c_bg = "var(--bg-card)"
            trend = ""
            sign = ""
        
        amount_text = f"{sign}{formatted_unreal} {currency_label}"
        pct_text = f"{trend}{abs(roi_pct):.2f}%"

    st.markdown(f'''
    <div class="cathay-card" style="background: {c_bg}; border-left: 6px solid {c_color}; padding: 20px; text-align: left; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); margin-bottom: 20px;">
        <div style="font-size: 14px; color: #94a3b8; margin-bottom: 12px;">{t("unrealized_pl")}</div>
        <div style="font-size: 24px; font-weight: bold; color: {c_color}; margin-bottom: 8px;">{amount_text}</div>
        <div style="font-size: 14px; font-weight: bold; color: {c_color};">{pct_text}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Removed P&L Waterfall Chart as requested

    if holdings.empty:
        st.markdown(f'''
        <div class="empty-state">
            <div class="empty-icon">🌱</div>
            <div class="empty-text">{t("portfolio_empty_desc")}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button(t("go_to_add_tx"), use_container_width=True):
            st.switch_page("views/02_transactions.py")

    if not holdings.empty and not is_loading_prices:
        st.markdown("<br>", unsafe_allow_html=True)
        lang = st.session_state.get("lang", "zh")
        news_title = "今日最新持股動態" if lang == "zh" else "Tin tức mới nhất về cổ phiếu"
        st.markdown(f"<h4 style='margin-left: 8px; margin-bottom: 16px;'>{news_title}</h4>", unsafe_allow_html=True)
        
        from news_utils import fetch_news
        
        # Get all current holdings where quantity > 0
        all_symbols = holdings[holdings["quantity"] > 0]["symbol"].tolist()
        
        all_news = []
        with st.spinner("Fetching latest news..." if lang == "zh" else "Đang tải tin tức..."):
            for symbol in all_symbols:
                all_news.extend(fetch_news(symbol, limit=2))
        
        if not all_news:
            search_txt = "前往 CafeF 搜尋" if lang == "zh" else "Tìm trên CafeF"
            st.markdown(f"""
            <div class="cathay-card" style="background: var(--bg-card); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 20px; text-align: center;">
                <span style="font-size: 15px; color: #94a3b8; display: block; margin-bottom: 10px;">
                    {"今日無相關新聞" if lang == "zh" else "Không có tin tức nào hôm nay"}
                </span>
                <a href="https://s.cafef.vn/tim-kiem.chn" target="_blank" style="color: #00F0FF; text-decoration: none; font-size: 15px; font-weight: bold; background: rgba(0, 240, 255, 0.1); padding: 8px 16px; border-radius: 20px;">
                    🔍 {search_txt}
                </a>
            </div>
            """, unsafe_allow_html=True)
        else:
            for item in all_news:
                st.markdown(f"""
                <div class="cathay-card" style="background: var(--bg-card); padding: 16px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 12px; display: flex; align-items: flex-start; gap: 16px;">
                    <div style="background: rgba(37, 99, 235, 0.2); border: 1px solid #2563eb; color: #60a5fa; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 14px; min-width: 65px; text-align: center; flex-shrink: 0; align-self: flex-start; margin-top: 2px;">
                        {item['symbol']}
                    </div>
                    <div>
                        <a href="{item['link']}" target="_blank" style="color: #ffffff; text-decoration: none; font-weight: bold; font-size: 16px; display: block; margin-bottom: 8px; line-height: 1.5; transition: color 0.2s;" onmouseover="this.style.color='#00F0FF'" onmouseout="this.style.color='#ffffff'">
                            {item['title']}
                        </a>
                        <div style="font-size: 13px; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
                            <span>🕒 {item['pubDate'][:16]}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
