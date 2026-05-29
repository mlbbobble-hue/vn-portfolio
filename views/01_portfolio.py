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
        val_str = f"{val:+,.0f}" if is_pl else f"{val:,.0f}"
        
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

st.markdown("<br>", unsafe_allow_html=True)
st.subheader(t("detail_holdings"))

table_rows = []
for _, row in portfolio_df.iterrows():
    bd = row.get("broker_breakdown", {})
    broker_str = " | ".join(f"{b}:{int(s):,}" for b, s in bd.items() if s > 0) if isinstance(bd, dict) else "-"
    cur = row["current_price"]; roi = row["roi_pct"]
    table_rows.append({
        t("symbol"):        row["symbol"],
        t("shares"):        f"{row['total_shares']:,.0f}",
        t("avg_cost"):      f"{row['avg_cost']:,.0f}",
        t("current_price"): f"{cur:,.0f}" if cur > 0 else "─",
        t("daily_change"):  f"{'▲'if row['change_pct']>0 else '▼'if row['change_pct']<0 else '─'} {abs(row['change_pct']):.2f}%",
        t("market_value"):  f"{row['market_value']:,.0f}",
        t("unrealized_pl"): f"{row['unrealized_pl']:+,.0f}",
        t("roi"):           f"{'+'if roi>=0 else ''}{roi:.2f}%",
        t("realized_pl"):   f"{row['realized_pl']:+,.0f}",
        t("broker_breakdown"): broker_str,
    })

disp = pd.DataFrame(table_rows)
def color_cell(val):
    if isinstance(val,str) and ("▲" in val or val.startswith("+")):
        return "color: var(--financial-up); font-weight: 600;"
    if isinstance(val,str) and ("▼" in val or (val.startswith("-") and any(c.isdigit() for c in val))):
        return "color: var(--financial-down); font-weight: 600;"
    return ""

styled = disp.style.map(color_cell, subset=[t("daily_change"), t("roi"), t("unrealized_pl"), t("realized_pl")])\
                   .hide(axis="index")
html_table = styled.to_html(classes="custom-table")
st.markdown(html_table, unsafe_allow_html=True)

# The ROI and Broker charts have been removed per user request.
