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
from portfolio import compute_portfolio_with_prices
from config import PRICE_REFRESH_SECONDS

st.markdown("""
<style>
/* 針對本頁面的微調 */
.app-title-small { font-size: 14px; color: rgba(255,255,255,0.8); margin-bottom: 4px; display:block; }
.empty-state { text-align: center; padding: 40px 20px; background: white; border-radius: 16px; border: 1px dashed #ccc; margin-top: 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; color: #ccc; }
.empty-text { color: #888; font-size: 16px; margin-bottom: 24px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    render_user_info_sidebar()

if not check_auth():
    st.stop()

# 獲取資料
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
    display_value = "🔄 價格同步中..."
    display_unrealized = "🔄 載入中..."
    display_roi = "🔄"
    st_autorefresh(interval=2000, limit=15, key="wait_for_prices")
else:
    display_value = f"₫{total_value:,.0f}"
    display_unrealized = f"₫{abs(total_unrealized):,.0f}"
    display_roi = f"{abs(roi_pct):.2f}%"

# 1. 國泰綠色頂部橫幅 (Cathay App Header)
st.markdown(f"""
<div class="cathay-app-header">
    <span class="app-title-small">我的資產總覽</span>
    <div class="total-value">{display_value}</div>
</div>
""", unsafe_allow_html=True)


# 2. 今日報酬與損益 (Badges & Cards)
st.markdown("<h4 style='margin-left: 8px;'>投資績效</h4>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    badge_class = "badge-up" if total_unrealized > 0 else "badge-down" if total_unrealized < 0 else "badge-neutral"
    sign = "+" if total_unrealized > 0 else ""
    st.markdown(f"""
    <div class="cathay-card">
        <div style="font-size: 14px; color: #888; margin-bottom: 8px;">未實現損益</div>
        <div style="font-size: 22px; font-weight: bold; color: #333;">{display_unrealized}</div>
        <div style="margin-top: 8px;"><span class="badge {badge_class}">{sign}{total_unrealized:,.0f}</span></div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    badge_class = "badge-up" if roi_pct > 0 else "badge-down" if roi_pct < 0 else "badge-neutral"
    sign = "+" if roi_pct > 0 else ""
    st.markdown(f"""
    <div class="cathay-card">
        <div style="font-size: 14px; color: #888; margin-bottom: 8px;">累積報酬率</div>
        <div style="font-size: 22px; font-weight: bold; color: #333;">{display_roi}</div>
        <div style="margin-top: 8px;"><span class="badge {badge_class}">{sign}{roi_pct:.2f}%</span></div>
    </div>
    """, unsafe_allow_html=True)

# 3. 資產分佈圖表 (隱藏 Modebar) 或 空狀態
if not holdings.empty:
    st.markdown("<h4 style='margin-left: 8px; margin-top: 16px;'>資產分佈</h4>", unsafe_allow_html=True)
    
    # 如果還沒抓到報價，就用總成本來畫圓餅圖
    plot_value_col = "market_value" if total_value > 0 else "total_cost"
    df_plot = holdings[holdings[plot_value_col] > 0]
    
    if not df_plot.empty:
        fig = px.pie(
            df_plot, 
            values=plot_value_col, 
            names="symbol", 
            hole=0.65,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(
            height=400,
            margin=dict(t=20, b=20, l=0, r=0),
            showlegend=True,
            legend=dict(
                title=None,
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=0.85
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        # 讓圓餅圖本身顯示百分比（太小的區塊會自動隱藏）
        fig.update_traces(
            textposition='inside', 
            textinfo='percent',
            hovertemplate="<b>%{label}</b><br>市值: ₫%{value:,.0f}<br>佔比: %{percent}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("👉 前往查看完整持股明細", use_container_width=True, type="primary"):
        st.switch_page("views/01_portfolio.py")
else:
    # 空白狀態
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🌱</div>
        <div class="empty-text">您目前尚未持有任何股票。<br>點擊下方按鈕開始您的第一筆交易紀錄！</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("前往新增交易", use_container_width=True):
            st.switch_page("views/02_transactions.py")
