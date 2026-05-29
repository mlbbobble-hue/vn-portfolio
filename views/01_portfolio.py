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
.acc-table {
    display: flex;
    flex-direction: column;
    background-color: var(--bg-card);
    border-radius: 12px;
    box-shadow: var(--shadow-soft);
    overflow: hidden;
    margin-bottom: 24px;
}
.acc-header {
    display: grid;
    grid-template-columns: 1.5fr 1fr 1fr 1.2fr;
    background-color: rgba(255,255,255,0.03);
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
}
.acc-row {
    display: grid;
    grid-template-columns: 1.5fr 1fr 1fr 1.2fr;
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
    align-items: center;
    transition: background-color 0.2s;
}
.acc-details summary {
    list-style: none;
    cursor: pointer;
}
.acc-details summary::-webkit-details-marker {
    display: none;
}
.acc-details summary:hover .acc-row {
    background-color: rgba(255,255,255,0.02);
}
.acc-details[open] summary .acc-arrow {
    transform: rotate(90deg);
}
.acc-arrow {
    display: inline-block;
    transition: transform 0.2s;
    margin-right: 6px;
    font-size: 12px;
    color: #94a3b8;
}
.acc-sub-row {
    display: grid;
    grid-template-columns: 1.5fr 1fr 1fr 1.2fr;
    padding: 16px 16px 16px 24px;
    background-color: #0f172a;
    border-bottom: 1px solid var(--border-color);
    align-items: center;
}
.acc-col-left { text-align: left; }
.acc-col-right { text-align: right; }

.tlt-main { font-size: 16px; color: #f8fafc; font-weight: 600; display: block; margin-bottom: 4px; }
.tlt-sub { font-size: 12px; color: #94a3b8; display: block; }
.tlt-pl-up { color: #10b981 !important; font-weight: 700; }
.tlt-pl-down { color: #ef4444 !important; font-weight: 700; }
.tlt-pl-neutral { color: #64748b !important; font-weight: 700; }
</style>

<div class="acc-table">
    <div class="acc-header">
        <div class="acc-col-left">標的</div>
        <div class="acc-col-right">持股</div>
        <div class="acc-col-right">市值</div>
        <div class="acc-col-right">損益</div>
    </div>
'''

def get_pl_classes(pl, roi):
    if pl > 0:
        return "tlt-pl-up", f"+{pl:,.0f}", f"+{roi:.2f}%"
    elif pl < 0:
        return "tlt-pl-down", f"{pl:,.0f}", f"{roi:.2f}%"
    else:
        return "tlt-pl-neutral", "0", "0.00%"

if portfolio_df.empty:
    html_str += '<div style="text-align:center; padding:24px; color:#94a3b8;">目前無任何持股資料</div>'
else:
    for _, row in portfolio_df.iterrows():
        sym = row["symbol"]
        bd = row.get("broker_breakdown", {})
        valid_brokers = {b: s for b, s in bd.items() if s > 0}
        
        cur = row["current_price"]
        cur_str = f"{cur:,.0f}" if cur > 0 else "─"
        avg_cost_val = row["avg_cost"]
        avg_cost_str = f"{avg_cost_val:,.0f}"
        
        shares_total = row['total_shares']
        mkt_val_total = row['market_value']
        pl_total = row["unrealized_pl"]
        roi_total = row["roi_pct"]
        
        pl_class, pl_str, roi_str = get_pl_classes(pl_total, roi_total)
        
        if len(valid_brokers) <= 1:
            # 單筆資料，一般行
            b_name = list(valid_brokers.keys())[0] if valid_brokers else "─"
            html_str += f"""
<div class="acc-row">
    <div class="acc-col-left">
        <span class="tlt-main">{sym}</span>
        <span class="tlt-sub">{b_name}</span>
    </div>
    <div class="acc-col-right">
        <span class="tlt-main">{shares_total:,.0f}</span>
        <span class="tlt-sub">現價: {cur_str}</span>
    </div>
    <div class="acc-col-right">
        <span class="tlt-main">{mkt_val_total:,.0f}</span>
        <span class="tlt-sub">成本: {avg_cost_str}</span>
    </div>
    <div class="acc-col-right">
        <span class="tlt-main {pl_class}">{pl_str}</span>
        <span class="tlt-sub {pl_class}">{roi_str}</span>
    </div>
</div>"""
        else:
            # 多筆資料，折疊行
            html_str += f"""
<details class="acc-details">
    <summary>
        <div class="acc-row">
            <div class="acc-col-left">
                <span class="tlt-main"><span class="acc-arrow">▶</span>{sym}</span>
                <span class="tlt-sub" style="margin-left: 16px;">多券商匯總</span>
            </div>
            <div class="acc-col-right">
                <span class="tlt-main">{shares_total:,.0f}</span>
                <span class="tlt-sub">現價: {cur_str}</span>
            </div>
            <div class="acc-col-right">
                <span class="tlt-main">{mkt_val_total:,.0f}</span>
                <span class="tlt-sub">成本: {avg_cost_str}</span>
            </div>
            <div class="acc-col-right">
                <span class="tlt-main {pl_class}">{pl_str}</span>
                <span class="tlt-sub {pl_class}">{roi_str}</span>
            </div>
        </div>
    </summary>"""
            
            # 子明細行
            for b_name, b_shares in valid_brokers.items():
                b_mkt = b_shares * cur
                b_cost = b_shares * avg_cost_val
                b_pl = b_mkt - b_cost if cur > 0 else 0
                b_roi = ((cur - avg_cost_val) / avg_cost_val * 100) if avg_cost_val > 0 and cur > 0 else 0
                
                b_pl_class, b_pl_str, b_roi_str = get_pl_classes(b_pl, b_roi)
                
                html_str += f"""
    <div class="acc-sub-row">
        <div class="acc-col-left">
            <span class="tlt-main" style="font-size:15px; color:#cbd5e1;">└ {sym}</span>
            <span class="tlt-sub" style="margin-left: 18px;">{b_name}</span>
        </div>
        <div class="acc-col-right">
            <span class="tlt-main" style="font-size:15px;">{b_shares:,.0f}</span>
            <span class="tlt-sub">現價: {cur_str}</span>
        </div>
        <div class="acc-col-right">
            <span class="tlt-main" style="font-size:15px;">{b_mkt:,.0f}</span>
            <span class="tlt-sub">成本: {avg_cost_str}</span>
        </div>
        <div class="acc-col-right">
            <span class="tlt-main {b_pl_class}" style="font-size:15px;">{b_pl_str}</span>
            <span class="tlt-sub {b_pl_class}">{b_roi_str}</span>
        </div>
    </div>"""
            
            html_str += "</details>"
            
html_str += "</div>"

st.markdown(html_str, unsafe_allow_html=True)
# The ROI and Broker charts have been removed per user request.
