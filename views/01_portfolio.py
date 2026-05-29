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

html_str = '''
<style>
.two-line-table {
    width: 100%;
    border-collapse: collapse;
    background-color: var(--bg-card);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 24px;
    box-shadow: var(--shadow-soft);
}
.two-line-table th {
    background-color: rgba(255,255,255,0.03);
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
}
.two-line-table td {
    padding: 16px 16px;
    border-bottom: 1px solid var(--border-color);
}
.two-line-table th:nth-child(1), .two-line-table td:nth-child(1) { text-align: left; }
.two-line-table th:nth-child(n+2), .two-line-table td:nth-child(n+2) { text-align: right; }

.tlt-main { font-size: 16px; color: #f8fafc; font-weight: 600; display: block; margin-bottom: 4px; }
.tlt-sub { font-size: 12px; color: #94a3b8; display: block; }

.tlt-pl-up { color: #10b981 !important; font-weight: 700; }
.tlt-pl-down { color: #ef4444 !important; font-weight: 700; }
.tlt-pl-neutral { color: #64748b !important; font-weight: 700; }
</style>
<table class="two-line-table">
    <thead>
        <tr>
            <th>標的</th>
            <th>持股</th>
            <th>市值</th>
            <th>損益</th>
        </tr>
    </thead>
    <tbody>
'''

if portfolio_df.empty:
    html_str += '<tr><td colspan="4" style="text-align:center; padding:24px; color:#94a3b8;">目前無任何持股資料</td></tr>'
else:
    for _, row in portfolio_df.iterrows():
        # 1. Broker
        bd = row.get("broker_breakdown", {})
        broker_str = " | ".join(f"{b}" for b, s in bd.items() if s > 0) if isinstance(bd, dict) and bd else "─"
        
        # 2. Price/Cost
        cur = row["current_price"]
        shares = f"{row['total_shares']:,.0f}"
        avg_cost = f"{row['avg_cost']:,.0f}"
        mkt_val = f"{row['market_value']:,.0f}"
        
        cur_str = f"{cur:,.0f}" if cur > 0 else "─"
        
        # 3. P&L
        pl = row["unrealized_pl"]
        roi = row["roi_pct"]
        
        if pl > 0:
            pl_class = "tlt-pl-up"
            pl_str = f"+{pl:,.0f}"
            roi_str = f"+{roi:.2f}%"
        elif pl < 0:
            pl_class = "tlt-pl-down"
            pl_str = f"{pl:,.0f}"
            roi_str = f"{roi:.2f}%"
        else:
            pl_class = "tlt-pl-neutral"
            pl_str = "0"
            roi_str = "0.00%"

        html_str += f"""
<tr>
    <td>
        <span class="tlt-main">{row["symbol"]}</span>
        <span class="tlt-sub">{broker_str}</span>
    </td>
    <td>
        <span class="tlt-main">{shares}</span>
        <span class="tlt-sub">現價: {cur_str}</span>
    </td>
    <td>
        <span class="tlt-main">{mkt_val}</span>
        <span class="tlt-sub">成本: {avg_cost}</span>
    </td>
    <td>
        <span class="tlt-main {pl_class}">{pl_str}</span>
        <span class="tlt-sub {pl_class}">{roi_str}</span>
    </td>
</tr>"""
        
html_str += "</tbody></table>"

st.markdown(html_str, unsafe_allow_html=True)
# The ROI and Broker charts have been removed per user request.
