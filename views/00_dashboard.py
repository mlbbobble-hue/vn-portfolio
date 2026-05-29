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
            
            def get_text_color(roi):
                if roi > 0: return "#10b981"
                if roi < 0: return "#ef4444"
                return "transparent"
                
            df_plot["pl_color"] = df_plot["roi_pct"].apply(get_text_color)
            
            df_plot["custom_txt"] = df_plot.apply(
                lambda r: f"<b>{r['symbol']}</b><br>{r['weight']:.1%}<br><span style='color:{r['pl_color']}; font-weight:600;'>{r['roi_pct']:+.2f}%</span>" if r['weight'] >= 0.01 else "",
                axis=1
            )

            st.markdown("<br>", unsafe_allow_html=True)
            
            df_plot["parent"] = ""
            fig = px.treemap(
                df_plot,
                names="symbol",
                parents="parent",
                values=plot_value_col,
                color="roi_pct",
                color_continuous_scale=[
                    [0.0, "#b91c1c"],     # 嚴重虧損 (<<0)
                    [0.499, "#7f1d1d"],   # 輕微虧損 (<0)
                    [0.5, "rgba(0,0,0,0)"],# 平盤 (=0) 完全透明
                    [0.501, "#10b981"],   # 穩定獲利 (>0)
                    [1.0, "#047857"]      # 巨額獲利 (>>50%)
                ],
                range_color=[-50, 50],
                custom_data=["roi_pct", "custom_txt"]
            )

            # Disable hover for the root node to prevent the empty tooltip
            import numpy as np
            if len(fig.data) > 0:
                parents = fig.data[0].parents
                hoverinfos = ["skip" if (p == "" or p is None) else "all" for p in parents]
                fig.data[0].hoverinfo = hoverinfos

            fig.update_layout(
                title=dict(
                    text=f"<b>{t('phs_asset_allocation')}</b>",
                    font=dict(size=18, color="#f8fafc"),
                    x=0.015,
                    y=0.96
                ),
                height=580,
                margin=dict(t=50, b=0, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
            )

            fig.update_traces(
                texttemplate="%{customdata[1]}",
                hovertemplate=t("portfolio_hover"),
                textfont=dict(color="#f8fafc", size=17),
                marker=dict(line=dict(width=2, color='#0f172a')),
                root_color="rgba(0,0,0,0)",
                tiling=dict(pad=0),
                pathbar=dict(visible=False)
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
