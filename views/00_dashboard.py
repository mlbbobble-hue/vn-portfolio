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
.app-title-small { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; display:block; }
.empty-state { text-align: center; padding: 40px 20px; background: var(--bg-card); border-radius: 12px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; color: var(--text-secondary); }
.empty-text { color: var(--text-secondary); font-size: 16px; margin-bottom: 24px; }
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
        <div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 8px;">未實現損益</div>
        <div style="font-size: 26px; font-weight: bold; color: var(--text-primary);">{display_unrealized}</div>
        <div style="margin-top: 8px;"><span class="badge {badge_class}">{sign}{total_unrealized:,.0f}</span></div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    badge_class = "badge-up" if roi_pct > 0 else "badge-down" if roi_pct < 0 else "badge-neutral"
    sign = "+" if roi_pct > 0 else ""
    st.markdown(f"""
    <div class="cathay-card">
        <div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 8px;">累積報酬率</div>
        <div style="font-size: 26px; font-weight: bold; color: var(--text-primary);">{display_roi}</div>
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
        # 定義分類函數與對應顏色
        def get_performance_category(roi):
            if roi >= 50: return "獲利翻倍 (>50%)"
            if roi > 0: return "穩定獲利 (>0%)"
            if roi < 0: return "微幅虧損 (<0%)"
            return "平盤或特殊 (0%)"

        df_plot = df_plot.copy()
        df_plot["performance"] = df_plot["roi_pct"].apply(get_performance_category)
        
        # 金融風專業配色
        color_map = {
            "獲利翻倍 (>50%)": "#10b981", # financial-up (Deep green is not specified in new rules, so use the exact up color)
            "穩定獲利 (>0%)": "#10b981",  # financial-up
            "微幅虧損 (<0%)": "#ef4444",  # financial-down
            "平盤或特殊 (0%)": "#64748b", # financial-none
            "(?)": "#1e293b"              # bg-card
        }

        fig = px.treemap(
            df_plot,
            path=[px.Constant("我的投資組合"), "symbol"],
            values=plot_value_col,
            color="performance",
            color_discrete_map=color_map,
            custom_data=["roi_pct"]
        )

        fig.update_layout(
            height=500,
            margin=dict(t=20, b=20, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            # 將圖例放在圖表右側，增加專業感
            legend=dict(
                title=None,
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02
            )
        )

        # 設定字體樣式與 Hover 效果
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>%{percentRoot:.2%}",
            hovertemplate="<b>%{label}</b><br>持股比例: %{percentRoot:.2%}<br>預估損益: %{customdata[0]:+.2f}%<extra></extra>",
            textfont=dict(color="white", size=15),
            marker=dict(line=dict(width=2, color='white')) # 增加格子之間的白色間距，提升質感
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
