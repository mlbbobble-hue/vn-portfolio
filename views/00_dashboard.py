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
    display_value = t("syncing_prices")
    display_unrealized = t("loading_values")
    display_roi = "🔄"
    st_autorefresh(interval=2000, limit=15, key="wait_for_prices")
else:
    display_value = f"₫{total_value:,.0f}"
    display_unrealized = f"₫{abs(total_unrealized):,.2f}"
    display_roi = f"{abs(roi_pct):.2f}%"


# 1. 頂部總資產橫幅
    st.markdown(f'''
    <div class="cathay-app-header" style="margin: 0 0 20px 0;">
        <span class="app-title-small">{t("my_assets_overview")}</span>
        <div class="total-value">{display_value}</div>
    </div>
    ''', unsafe_allow_html=True)

    # 2. 投資績效 Badges & Cards
    st.markdown(f"<h4 style='margin-left: 8px;'>{t('invest_performance')}</h4>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        badge_class = "badge-up" if total_unrealized > 0 else "badge-down" if total_unrealized < 0 else "badge-neutral"
        sign = "+" if total_unrealized > 0 else ""
        st.markdown(f'''
        <div class="cathay-card">
            <div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 8px;">{t("unrealized_pl")}</div>
            <div style="font-size: 26px; font-weight: bold; color: var(--text-primary);">{display_unrealized}</div>
            <div style="margin-top: 8px;"><span class="badge {badge_class}">{sign}{total_unrealized:,.2f}</span></div>
        </div>
        ''', unsafe_allow_html=True)

    with c2:
        badge_class = "badge-up" if roi_pct > 0 else "badge-down" if roi_pct < 0 else "badge-neutral"
        sign = "+" if roi_pct > 0 else ""
        st.markdown(f'''
        <div class="cathay-card">
            <div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 8px;">{t("accum_return_rate")}</div>
            <div style="font-size: 26px; font-weight: bold; color: var(--text-primary);">{display_roi}</div>
            <div style="margin-top: 8px;"><span class="badge {badge_class}">{sign}{roi_pct:.2f}%</span></div>
        </div>
        ''', unsafe_allow_html=True)

    # 3. 資產分佈圖表 (Treemap) 或 空狀態
    if not holdings.empty:
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        
        plot_value_col = "market_value" if total_value > 0 else "total_cost"
        df_plot = holdings[holdings[plot_value_col] > 0]
        
        if not df_plot.empty:
            df_plot = df_plot.copy()
            total_val = df_plot[plot_value_col].sum()
            df_plot["weight"] = df_plot[plot_value_col] / total_val
            df_plot["weight_pct"] = df_plot["weight"] * 100

            import plotly.graph_objects as go
            import numpy as np

            # 準備氣泡顏色
            colors = []
            for roi in df_plot["roi_pct"]:
                if roi > 0:
                    colors.append("rgba(16, 185, 129, 0.8)")  # 獲利綠
                elif roi < 0:
                    colors.append("rgba(239, 68, 68, 0.8)")   # 虧損紅
                else:
                    colors.append("rgba(100, 116, 139, 0.8)")  # 中性灰

            # 準備氣泡大小：以最大市值股票為基準 [25, 80]
            max_val = df_plot[plot_value_col].max()
            if max_val > 0:
                sizes = 25 + 55 * (df_plot[plot_value_col] / max_val)
            else:
                sizes = [40] * len(df_plot)

            # 準備置中粗體股票代碼文字
            labels = [f"<b>{sym}</b>" for sym in df_plot["symbol"]]

            # 多國語言支持
            lang = st.session_state.get("lang", "zh")
            title_text = "投資組合效率前緣邊界分析圖" if lang == "zh" else "Phân tích biên hiệu quả danh mục đầu tư"
            x_title = "持股比例 (%)" if lang == "zh" else "Tỷ lệ (%)"
            y_title = "未實現損益率 (%)" if lang == "zh" else "Hiệu suất (%)"

            if lang == "vi":
                ht = (
                    "<b>Mã CK: %{customdata[0]}</b><br>"
                    "Tỷ lệ: %{x:.2f}%<br>"
                    "Hiệu suất: %{y:+.2f}%<br>"
                    "Tổng giá trị: ₫%{customdata[1]:,.0f}"
                    "<extra></extra>"
                )
            else:
                ht = (
                    "<b>股票代碼: %{customdata[0]}</b><br>"
                    "持股比例: %{x:.2f}%<br>"
                    "未實現損益率: %{y:+.2f}%<br>"
                    "目前總市值: ₫%{customdata[1]:,.0f}"
                    "<extra></extra>"
                )

            st.markdown("<br>", unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_plot["weight_pct"],
                y=df_plot["roi_pct"],
                mode="markers+text",
                marker=dict(
                    size=sizes,
                    color=colors,
                    line=dict(width=1.5, color="#f8fafc")
                ),
                text=labels,
                textposition="middle center",
                textfont=dict(
                    color="#f8fafc",
                    size=12,
                    family="Noto Sans TC"
                ),
                customdata=np.stack((df_plot["symbol"], df_plot[plot_value_col]), axis=-1),
                hovertemplate=ht
            ))

            fig.update_layout(
                title=dict(
                    text=f"<b>{title_text}</b>",
                    font=dict(size=18, color="#f8fafc"),
                    x=0.015,
                    y=0.96
                ),
                height=580,
                margin=dict(t=80, b=50, l=50, r=30),
                paper_bgcolor="#0f172a",
                plot_bgcolor="#0f172a",
                xaxis=dict(
                    title=dict(text=x_title, font=dict(color="#94a3b8", size=13)),
                    tickfont=dict(color="#94a3b8"),
                    gridcolor="#334155",
                    zeroline=True,
                    zerolinecolor="#334155",
                    zerolinewidth=1.5,
                    range=[0, max(50, df_plot["weight_pct"].max() + 5)]
                ),
                yaxis=dict(
                    title=dict(text=y_title, font=dict(color="#94a3b8", size=13)),
                    tickfont=dict(color="#94a3b8"),
                    gridcolor="#334155",
                    zeroline=True,
                    zerolinecolor="#334155",
                    zerolinewidth=2
                ),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})
            
    else:
        st.markdown(f'''
        <div class="empty-state">
            <div class="empty-icon">🌱</div>
            <div class="empty-text">{t("portfolio_empty_desc")}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button(t("go_to_add_tx"), use_container_width=True):
            st.switch_page("views/02_transactions.py")
