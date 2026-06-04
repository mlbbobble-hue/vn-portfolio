"""頁面1：持倉總覽（雙語 + Supabase Auth）"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import get_all_transactions, get_price_cache
from portfolio import compute_holdings, compute_portfolio_with_prices

st.set_page_config(page_title=f"VN Portfolio | {t('portfolio_title')}", page_icon="💼", layout="wide")

from theme import load_css
load_css()

if not check_auth():
    st.stop()

st.markdown(f"""
<div class="page-header">
    <h2>{t('portfolio_title')}</h2>
    <p>{t('portfolio_desc')}</p>
</div>""", unsafe_allow_html=True)

txns = get_all_transactions()
brokers = [t("all")] + (list(txns["broker"].unique()) if not txns.empty else [])
selected_broker = st.selectbox(t("filter_broker"), brokers)

holdings    = compute_holdings()
price_cache = get_price_cache()
portfolio_df= compute_portfolio_with_prices(holdings, price_cache)

if not portfolio_df.empty and selected_broker != t("all"):
    def has_broker(bd):
        return selected_broker in bd if isinstance(bd, dict) else False
    portfolio_df = portfolio_df[portfolio_df["broker_breakdown"].apply(has_broker)]

if portfolio_df.empty:
    st.info(t("no_data"))
    st.stop()

total_cost   = portfolio_df["total_cost"].sum()
total_mktval = portfolio_df["market_value"].sum()
total_unreal = portfolio_df["unrealized_pl"].sum()
total_real   = portfolio_df["realized_pl"].sum()
total_roi    = ((total_mktval - total_cost) / total_cost * 100) if total_cost > 0 else 0

c1, c2, c3, c4 = st.columns(4)
for col, label, val, suffix, color in [
    (c1, t("total_invested"), total_cost,   t("vnd"), "#a78bfa"),
    (c2, t("current_value"), total_mktval,  t("vnd"), "#a78bfa"),
    (c3, t("unrealized_pl"), total_unreal,  f"{'▲'if total_unreal>=0 else '▼'} {abs(total_roi):.2f}%",
     "var(--financial-up)" if total_unreal>=0 else "var(--financial-down)"),
    (c4, t("realized_pl"),  total_real,     t("history_pl"),
     "var(--financial-up)" if total_real>=0 else "var(--financial-down)"),
]:
    with col:
        is_pl = '損益' in label or 'Lãi' in label
        val_str = f"{val:+,.2f}" if is_pl else f"{val:,.0f}"
        
        # 依照規格：標題 14px (--text-secondary)，數值 26px bold
        # 如果是損益則套用 --financial-up/down，否則套用 --text-primary
        if color == "#a78bfa":
            val_color = "var(--text-primary)"
        else:
            val_color = color
            
        st.markdown(f"""
        <div class="metric-card">
            <div style='font-size:14px;color:var(--text-secondary);'>{label}</div>
            <div style='font-size:26px;font-weight:bold;color:{val_color};margin-top:4px;'>{val_str}</div>
            <div style='font-size:12px;color:var(--text-secondary);margin-top:4px;'>{suffix}</div>
        </div>""", unsafe_allow_html=True)


if not portfolio_df.empty:
    df_for_charts = portfolio_df[portfolio_df["market_value"] > 0]
    
    if not df_for_charts.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- Treemap (Portfolio Heatmap) ---
        plot_value_col = "market_value" if df_for_charts["market_value"].sum() > 0 else "total_cost"
        df_plot = df_for_charts[df_for_charts[plot_value_col] > 0]
        
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
                color_continuous_scale=[(0, "#9D4EDD"), (0.5, "rgba(20, 18, 38, 0.6)"), (1, "#FF2A85")],
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
                    font=dict(size=18, color="#FFFFFF"),
                    x=0.015,
                    y=0.96
                ),
                height=580,
                margin=dict(t=80, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
            )
            
            st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);'>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.subheader(t("detail_holdings"))


if portfolio_df.empty:
    st.info(t("no_data"))
else:
    display_df = portfolio_df.copy()
    
    # Define columns to show
    show_cols = ["symbol", "total_shares", "current_price", "avg_cost", "market_value", "unrealized_pl", "roi_pct"]
    display_df = display_df[show_cols]
    
    # Use Pandas styler to add colors to profit/loss columns
    def color_pl(val):
        try:
            v = float(val)
            if v > 0:
                return 'color: #10b981; font-weight: bold;'
            elif v < 0:
                return 'color: #ef4444; font-weight: bold;'
        except:
            pass
        return 'color: #64748b;'

    styled_df = display_df.style.map(color_pl, subset=['unrealized_pl', 'roi_pct'])

    st.dataframe(
        styled_df,
        column_config={
            "symbol": st.column_config.TextColumn("標的 (Symbol)", width="small"),
            "total_shares": st.column_config.NumberColumn("持股 (Shares)", format="%d"),
            "current_price": st.column_config.NumberColumn("現價 (Current)", format="₫ %d"),
            "avg_cost": st.column_config.NumberColumn("成本 (Avg Cost)", format="₫ %d"),
            "market_value": st.column_config.NumberColumn("市值 (Market Value)", format="₫ %d"),
            "unrealized_pl": st.column_config.NumberColumn("損益 (P/L)", format="₫ %d"),
            "roi_pct": st.column_config.NumberColumn("損益率 (ROI %)", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True
    )
