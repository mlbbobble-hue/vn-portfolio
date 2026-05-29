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

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);color:#e2e8f0;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1e1e3a 0%,#16213e 100%);border-right:1px solid rgba(99,102,241,0.2);}
.metric-card{background:linear-gradient(135deg,rgba(30,30,60,0.8),rgba(20,20,45,0.9));border:1px solid rgba(99,102,241,0.3);border-radius:16px;padding:18px 22px;margin:6px 0;}
.stButton>button{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border:none;border-radius:8px;font-weight:500;}
.stButton>button[kind="secondary"]{background:transparent!important;border:1px solid rgba(99,102,241,0.4)!important;color:#a78bfa!important;}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    render_lang_switcher()
    st.divider()
    render_user_info_sidebar()

if not check_auth():
    st.stop()

st.markdown(f"""
<div style='background:linear-gradient(90deg,rgba(99,102,241,0.15) 0%,transparent 100%);
            border-left:4px solid #6366f1;padding:12px 20px;border-radius:0 12px 12px 0;margin-bottom:24px;'>
    <h2 style='margin:0;color:#e2e8f0;'>{t('portfolio_title')}</h2>
    <p style='margin:4px 0 0;color:#94a3b8;font-size:0.9rem;'>{t('portfolio_desc')}</p>
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
     "#34d399" if total_unreal>=0 else "#f87171"),
    (c4, t("realized_pl"),  total_real,     t("history_pl"),
     "#34d399" if total_real>=0 else "#f87171"),
]:
    with col:
        is_pl = '損益' in label or 'Lãi' in label
        val_str = f"{val:+,.0f}" if is_pl else f"{val:,.0f}"
        st.markdown(f"""
        <div class="metric-card">
            <div style='font-size:.82rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;'>{label}</div>
            <div style='font-size:1.6rem;font-weight:700;color:{color};'>{val_str}</div>
            <div style='font-size:.82rem;color:#64748b;'>{suffix}</div>
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
        return "color:#34d399;font-weight:600"
    if isinstance(val,str) and ("▼" in val or (val.startswith("-") and any(c.isdigit() for c in val))):
        return "color:#f87171;font-weight:600"
    return "color:#e2e8f0"

styled = disp.style.map(color_cell, subset=[t("daily_change"), t("roi"), t("unrealized_pl"), t("realized_pl")])
st.dataframe(styled, use_container_width=True, height=300)

st.markdown("<br>", unsafe_allow_html=True)
col_l, col_r = st.columns(2)
with col_l:
    st.subheader(t("roi_ranking"))
    roi_df = portfolio_df[portfolio_df["current_price"]>0].sort_values("roi_pct", ascending=True)
    if not roi_df.empty:
        fig = go.Figure(go.Bar(
            x=roi_df["roi_pct"], y=roi_df["symbol"], orientation="h",
            marker_color=["#34d399" if v>=0 else "#f87171" for v in roi_df["roi_pct"]],
            text=[f"{v:+.2f}%" for v in roi_df["roi_pct"]], textposition="outside",
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#e2e8f0"), height=280,
                          xaxis=dict(gridcolor="rgba(99,102,241,0.1)", title="ROI %"),
                          margin=dict(t=10,b=10,l=10,r=60), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.subheader(t("broker_distribution"))
    broker_totals = {}
    for _, row in portfolio_df.iterrows():
        bd = row.get("broker_breakdown", {}); mkt = row["market_value"]; total_s = row["total_shares"]
        if isinstance(bd, dict) and total_s > 0:
            for b, s in bd.items():
                broker_totals[b] = broker_totals.get(b,0) + mkt * s/total_s
    if broker_totals:
        bf = pd.DataFrame(list(broker_totals.items()), columns=[t("broker"), t("market_value")])
        fig2 = px.pie(bf, values=t("market_value"), names=t("broker"), hole=0.5,
                      color_discrete_sequence=["#6366f1","#8b5cf6","#a78bfa","#c4b5fd"])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                           height=280, margin=dict(t=10,b=10), showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)
