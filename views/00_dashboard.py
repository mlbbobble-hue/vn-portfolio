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
    show_in_twd = st.toggle("顯示為台幣 (TWD) 🇹🇼", value=False)
    
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
            c_color = "#8A9A5B"
            c_bg = "var(--bg-card)"
            trend = "▲ "
            sign = "+"
        elif total_unrealized < 0:
            c_color = "#C97A7E"
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
    
    # 2.5 瀑布圖 (P&L Waterfall Chart)
    if not is_loading_prices and not holdings.empty:
        import plotly.graph_objects as go
        from datetime import date
        
        total_realized_pl = get_total_realized_pl()
        total_cash_div = 0.0
        total_stock_div_val = 0.0
        
        _, _, div_details = compute_received_dividends()
        if div_details:
            price_cache_df = get_price_cache()
            price_cache = price_cache_df.set_index("symbol")["price"].to_dict() if not price_cache_df.empty else {}
            
            for div in div_details:
                pay_date = div.get("pay_date", "")
                is_done = False
                if pay_date and pd.notnull(pay_date) and str(pay_date).strip():
                    try:
                        pdt = pd.to_datetime(pay_date).date()
                        is_done = pdt <= date.today()
                    except:
                        pass
                if is_done:
                    if div["type"] == "CASH":
                        total_cash_div += div.get("cash_received", 0)
                    elif div["type"] == "STOCK":
                        sym = div["symbol"]
                        curr_price = price_cache.get(sym, 0)
                        total_stock_div_val += div.get("stock_received", 0) * curr_price
                        
        divisor = EXCHANGE_RATE if show_in_twd else 1
        val_cost = total_cost / divisor
        val_realized = total_realized_pl / divisor
        val_unrealized = total_unrealized / divisor
        val_cash_div = total_cash_div / divisor
        val_stock_div = total_stock_div_val / divisor
        total_worth = val_cost + val_realized + val_unrealized + val_cash_div + val_stock_div
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="P&L", orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["當前投入本金", "已實現損益", "未實現損益", "現金配息", "配股現值", "總經濟價值"],
            textposition="outside",
            text=[f"{v:,.0f}" for v in [val_cost, val_realized, val_unrealized, val_cash_div, val_stock_div, total_worth]],
            y=[val_cost, val_realized, val_unrealized, val_cash_div, val_stock_div, 0],
            connector={"line":{"color":"#C2B8AD", "dash":"dot"}},
            decreasing={"marker":{"color":"#C97A7E"}},
            increasing={"marker":{"color":"#8A9A5B"}},
            totals={"marker":{"color":"#8BA3C7", "line": {"color":"#6D85AB", "width":1}}}
        ))
        
        lang = st.session_state.get("lang", "zh")
        wf_title = "損益瀑布圖 (P&L Waterfall)" if lang == "zh" else "Biểu đồ Thác nước Lãi/Lỗ"
        
        fig_waterfall.update_layout(
            title=dict(text=f"<b>{wf_title}</b>", font=dict(size=18, color="#4A4A4A"), x=0.015, y=0.9),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8C8C8C"),
            margin=dict(t=60, b=40, l=40, r=40),
            height=420,
            showlegend=False,
            yaxis=dict(zeroline=True, zerolinecolor="#E6E1D8", gridcolor="#F2EDE4"),
            xaxis=dict(gridcolor="#F2EDE4")
        )
        st.plotly_chart(fig_waterfall, use_container_width=True, config={'displayModeBar': False})

    # 3. 資產分佈圖表 (Treemap) 或 空狀態
    if not holdings.empty:
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        
        plot_value_col = "market_value" if total_value > 0 else "total_cost"
        df_plot = holdings[holdings[plot_value_col] > 0]
        
        if not df_plot.empty:
            df_plot = df_plot.copy()
            total_val = df_plot[plot_value_col].sum()
            df_plot["weight"] = df_plot[plot_value_col] / total_val
            df_plot["weight_pct"] = (df_plot["weight"] * 100).round(2)
            df_plot["roi_pct"] = df_plot["roi_pct"].astype(float).round(2)

            df_plot["weight_str"] = df_plot["weight_pct"].apply(lambda x: f"{x:.2f}%")
            df_plot["roi_str"] = df_plot["roi_pct"].apply(lambda x: f"{x:+.2f}%")
            df_plot["val_str"] = df_plot[plot_value_col].apply(lambda x: f"{x:,.0f}")

            import plotly.express as px
            import pandas as pd

            lang = st.session_state.get("lang", "zh")
            title_text = "投資組合熱力圖" if lang == "zh" else "Bản đồ nhiệt danh mục đầu tư"
            
            if lang == "vi":
                ht = (
                    "<b>Mã CK: %{customdata[0]}</b><br>"
                    "Tỷ lệ: %{customdata[1]}<br>"
                    "Hiệu suất: %{customdata[2]}<br>"
                    "Tổng giá trị: ₫%{customdata[3]}"
                    "<extra></extra>"
                )
            else:
                ht = (
                    "<b>股票代碼: %{customdata[0]}</b><br>"
                    "持股比例: %{customdata[1]}<br>"
                    "未實現損益率: %{customdata[2]}<br>"
                    "目前總市值: ₫%{customdata[3]}"
                    "<extra></extra>"
                )

            # Add color logic for treemap
            df_plot["color_val"] = df_plot["roi_pct"].clip(-20, 20)  # For color scale clipping

            fig = px.treemap(
                df_plot,
                path=[px.Constant("Portfolio"), "symbol"],
                values=plot_value_col,
                color="color_val",
                color_continuous_scale=[(0, "#C97A7E"), (0.5, "#E6E1D8"), (1, "#8A9A5B")],
                color_continuous_midpoint=0,
                custom_data=["symbol", "weight_str", "roi_str", "val_str"]
            )
            
            fig.update_traces(
                textinfo="label+value+text",
                text=df_plot["roi_str"],
                hovertemplate=ht
            )

            fig.update_layout(
                title=dict(
                    text=f"<b>{title_text}</b>",
                    font=dict(size=18, color="#4A4A4A"),
                    x=0.015,
                    y=0.96
                ),
                height=580,
                margin=dict(t=80, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
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
