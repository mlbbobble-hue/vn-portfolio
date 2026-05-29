from theme import load_css
load_css()
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from i18n import t
from db_router import seed_test_data, get_price_cache
from portfolio import compute_holdings, compute_portfolio_with_prices
from config import PRICE_REFRESH_SECONDS

def fmt_vnd(v): 
    if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.2f} tỷ"
    if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M"
    return f"{v:,.0f}"

def fmt_pct(v):
    return f"{'▲' if v>0 else '▼' if v<0 else '─'} {abs(v):.2f}%"

st.markdown(f"""
<div class="page-header">
    <h1>{t('dashboard_title')}</h1>
    <p>{t('dashboard_desc')}</p>
</div>
""", unsafe_allow_html=True)

seed_test_data()

holdings = compute_holdings()
price_cache = get_price_cache()
portfolio_df = compute_portfolio_with_prices(holdings, price_cache)
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if not portfolio_df.empty:
    total_cost   = portfolio_df["total_cost"].sum()
    total_mktval = portfolio_df["market_value"].sum()
    total_unreal = portfolio_df["unrealized_pl"].sum()
    total_real   = portfolio_df["realized_pl"].sum()
    total_roi    = ((total_mktval - total_cost) / total_cost * 100) if total_cost > 0 else 0
    has_price    = portfolio_df[portfolio_df["current_price"] > 0]
    up_count     = len(has_price[has_price["change_pct"] > 0])
    down_count   = len(has_price[has_price["change_pct"] < 0])

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, label, val, sub, color in [
        (c1, t("total_market_value"), total_mktval, t("vnd"), "#a78bfa"),
        (c2, t("unrealized_pl"), total_unreal, fmt_pct(total_roi),
         "#34d399" if total_unreal >= 0 else "#f87171"),
        (c3, t("realized_pl"), total_real, t("history_pl"),
         "#34d399" if total_real >= 0 else "#f87171"),
        (c4, t("positions_count"), len(portfolio_df), "", "#a78bfa"),
        (c5, t("today_updown"), up_count, f"▼ {down_count}", "#34d399"),
    ]:
        sign = "+" if "損益" in label or "Lãi" in label and val > 0 else ""
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{color};">
                    {sign if val > 0 and '損益' in label or 'Lãi' in label else ''}{fmt_vnd(val) if isinstance(val,float) else val}
                </div>
                <div class="metric-sub" style="color:{color if '損益' in label or 'Lãi' in label else '#64748b'};">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.subheader(t("pl_by_stock"))
        display_df = portfolio_df[portfolio_df["current_price"] > 0].copy()
        if not display_df.empty:
            fig = go.Figure(go.Bar(
                x=display_df["symbol"],
                y=display_df["unrealized_pl"] / 1_000_000,
                marker_color=["#34d399" if v >= 0 else "#f87171" for v in display_df["unrealized_pl"]],
                text=[f"{r:+.1f}%" for r in display_df["roi_pct"]],
                textposition="outside",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis=dict(gridcolor="rgba(99,102,241,0.1)"),
                yaxis=dict(gridcolor="rgba(99,102,241,0.1)", title="M VNĐ"),
                height=320, margin=dict(t=20, b=20, l=10, r=10), showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader(t("portfolio_weight"))
        pie_df = portfolio_df[portfolio_df["market_value"] > 0]
        if not pie_df.empty:
            fig2 = px.pie(pie_df, values="market_value", names="symbol", hole=0.55,
                          color_discrete_sequence=px.colors.sequential.Plasma_r)
            fig2.update_traces(textposition="outside", textinfo="label+percent")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                               height=320, margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader(t("quick_overview"))
    tbl = portfolio_df.copy()
    tbl["chg_str"] = tbl["change_pct"].apply(lambda x: f"{'▲' if x>0 else '▼' if x<0 else '─'} {abs(x):.2f}%")
    tbl["roi_str"] = tbl["roi_pct"].apply(lambda x: f"{'+'if x>=0 else ''}{x:.2f}%")
    cols_map = {
        "symbol": t("symbol"), "total_shares": t("shares"),
        "avg_cost": t("avg_cost"), "current_price": t("current_price"),
        "chg_str": t("daily_change"), "market_value": t("market_value"),
        "unrealized_pl": t("unrealized_pl"), "roi_str": t("roi"),
    }
    disp = tbl[[c for c in cols_map if c in tbl.columns]].rename(columns=cols_map)

    def style_cell(val):
        if isinstance(val, str) and ("▲" in val or val.startswith("+")):
            return "color:#34d399"
        if isinstance(val, str) and ("▼" in val or (val.startswith("-") and "%" in val)):
            return "color:#f87171"
        return ""

    styled = (disp.style
              .format({t("shares"):"{:,.0f}", t("avg_cost"):"{:,.0f}",
                       t("current_price"):"{:,.0f}", t("market_value"):"{:,.0f}",
                       t("unrealized_pl"):"{:+,.0f}"})
              .map(style_cell, subset=[t("daily_change"), t("roi")]))
    st.dataframe(styled, use_container_width=True, height=260)

else:
    st.info(t("no_data"))
    if st.button(t("load_test_data")):
        seed_test_data()
        st.rerun()

st.markdown(f"""
<div style='text-align:right;color:#475569;font-size:0.78rem;margin-top:16px;'>
    {t("last_updated", time=now_str)} • {t("auto_refresh", n=PRICE_REFRESH_SECONDS)}
</div>
""", unsafe_allow_html=True)
