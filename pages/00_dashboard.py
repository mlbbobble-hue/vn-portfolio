"""
頁面0：首頁總覽 (Dashboard) - 國泰手機 App 風格
"""
from theme import load_css
load_css()
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from i18n import t
from auth_page import check_auth, render_user_info_sidebar
from portfolio import compute_portfolio_with_prices
from config import PRICE_REFRESH_SECONDS

st.markdown("""
<style>
/* 針對本頁面的微調 */
.app-title-small { font-size: 14px; color: rgba(255,255,255,0.8); margin-bottom: 4px; display:block; }
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

# 1. 國泰綠色頂部橫幅 (Cathay App Header)
st.markdown(f"""
<div class="cathay-app-header">
    <span class="app-title-small">我的資產總覽</span>
    <div class="total-value">₫{total_value:,.0f}</div>
</div>
""", unsafe_allow_html=True)



# 3. 今日報酬與損益 (Badges & Cards)
st.markdown("<h4 style='margin-left: 8px;'>投資績效</h4>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    badge_class = "badge-up" if total_unrealized > 0 else "badge-down" if total_unrealized < 0 else "badge-neutral"
    sign = "+" if total_unrealized > 0 else ""
    st.markdown(f"""
    <div class="cathay-card">
        <div style="font-size: 14px; color: #888; margin-bottom: 8px;">未實現損益</div>
        <div style="font-size: 22px; font-weight: bold; color: #333;">₫{abs(total_unrealized):,.0f}</div>
        <div style="margin-top: 8px;"><span class="badge {badge_class}">{sign}{total_unrealized:,.0f}</span></div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    badge_class = "badge-up" if roi_pct > 0 else "badge-down" if roi_pct < 0 else "badge-neutral"
    sign = "+" if roi_pct > 0 else ""
    st.markdown(f"""
    <div class="cathay-card">
        <div style="font-size: 14px; color: #888; margin-bottom: 8px;">累積報酬率</div>
        <div style="font-size: 22px; font-weight: bold; color: #333;">{abs(roi_pct):.2f}%</div>
        <div style="margin-top: 8px;"><span class="badge {badge_class}">{sign}{roi_pct:.2f}%</span></div>
    </div>
    """, unsafe_allow_html=True)

# 4. 資產分佈圖表 (隱藏 Modebar)
if not holdings.empty and total_value > 0:
    st.markdown("<h4 style='margin-left: 8px; margin-top: 16px;'>資產分佈</h4>", unsafe_allow_html=True)
    df_plot = holdings[holdings["market_value"] > 0]
    if not df_plot.empty:
        fig = px.pie(
            df_plot, 
            values="market_value", 
            names="symbol", 
            hole=0.6,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
