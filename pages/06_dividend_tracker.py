"""頁面6：配息追蹤 (The Dividend Tracker)"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from portfolio import compute_portfolio_with_prices
from db_router import get_dividend_events

st.set_page_config(page_title=f"VN Portfolio | {t('nav_div_tracker')}", page_icon="💰", layout="wide")

# The Dividend Tracker CSS Aesthetics
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Urbanist', sans-serif;
}
.stApp {
    background: linear-gradient(135deg, #001F29 0%, #004B5E 50%, #F5F7FA 100%);
    color: #071317;
}
/* For dark mode */
@media (prefers-color-scheme: dark) {
    .stApp {
        background: linear-gradient(180deg, #021c23 0%, #063442 100%);
        color: #F7F9FC;
    }
}
.dt-header {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(180deg, #FFFFFF 0%, #00d2ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.metric-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    text-align: center;
    transition: transform 0.2s ease-in-out;
}
.metric-card:hover {
    transform: translateY(-5px);
}
.metric-label {
    font-size: 1.1rem;
    color: #B5ECFF;
    font-weight: 600;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #FFFFFF;
}
.metric-value.highlight {
    background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.chart-container {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 20px;
    margin-top: 2rem;
}
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    render_lang_switcher()
    st.divider()
    render_user_info_sidebar()

if not check_auth():
    st.stop()

st.markdown(f"<div class='dt-header'>{t('nav_div_tracker')}</div>", unsafe_allow_html=True)
st.markdown(f"<p style='color: #8be1f6; font-size: 1.1rem;'>{t('dividends_desc')}</p>", unsafe_allow_html=True)

# 1. Fetch Data
holdings = compute_portfolio_with_prices()
events = get_dividend_events()

if holdings.empty:
    st.info(t("no_data"))
    st.stop()

# 2. Calculate Key Metrics
total_value = holdings['market_value'].sum()
total_cost = holdings['total_cost'].sum()

# TTM (Trailing 12 Months) logic
one_year_ago = pd.Timestamp(date.today() - timedelta(days=365))
events_ttm = pd.DataFrame()

if not events.empty:
    events['ex_date_dt'] = pd.to_datetime(events['ex_date'], errors='coerce')
    events_ttm = events[(events['type'] == 'CASH') & (events['ex_date_dt'] >= one_year_ago)].copy()

annual_income = 0.0
ttm_dps_map = {}

# Map current shares
shares_map = holdings.set_index("symbol")["total_shares"].to_dict()
price_map = holdings.set_index("symbol")["current_price"].to_dict()
avg_cost_map = holdings.set_index("symbol")["avg_cost"].to_dict()

if not events_ttm.empty:
    for sym in shares_map.keys():
        sym_events = events_ttm[events_ttm['symbol'] == sym]
        dps = sym_events['cash_amount'].sum()
        ttm_dps_map[sym] = dps
        annual_income += dps * shares_map[sym]

yoc = (annual_income / total_cost * 100) if total_cost > 0 else 0.0
portfolio_yield = (annual_income / total_value * 100) if total_value > 0 else 0.0

# 3. Top Metrics Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{t('dt_annual_income')}</div>
        <div class="metric-value highlight">₫{annual_income:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{t('dt_yoc')}</div>
        <div class="metric-value">{yoc:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{t('dt_yield')}</div>
        <div class="metric-value">{portfolio_yield:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{t('dt_portfolio_value')}</div>
        <div class="metric-value">₫{total_value:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 4. Monthly Calendar Bar Chart
st.markdown(f"### 📅 {t('dt_monthly_calendar')}")
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
if not events_ttm.empty:
    # Project historical TTM into a monthly layout for the current portfolio
    monthly_data = []
    for _, row in events_ttm.iterrows():
        sym = row['symbol']
        if sym in shares_map:
            inc = row['cash_amount'] * shares_map[sym]
            month_str = row['ex_date_dt'].strftime("%Y-%m")
            monthly_data.append({"Month": month_str, "Income": inc, "Symbol": sym})
    
    if monthly_data:
        df_month = pd.DataFrame(monthly_data)
        df_grouped = df_month.groupby(["Month", "Symbol"])["Income"].sum().reset_index()
        df_grouped = df_grouped.sort_values("Month")
        
        fig = px.bar(
            df_grouped, x="Month", y="Income", color="Symbol",
            color_discrete_sequence=px.colors.qualitative.Prism,
            text_auto='.2s'
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#ffffff",
            xaxis_title="",
            yaxis_title=t('dt_amount'),
            margin=dict(l=20, r=20, t=20, b=20),
            hovermode="x unified",
            barmode="stack"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("no_data"))
else:
    st.info(t("no_data"))
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 5. Holdings Breakdown Table
st.markdown(f"### 📋 {t('dt_holdings_breakdown')}")
rows = []
for sym, shares in shares_map.items():
    if shares > 0:
        dps = ttm_dps_map.get(sym, 0.0)
        cost = avg_cost_map.get(sym, 0.0)
        price = price_map.get(sym, 0.0)
        
        inc = dps * shares
        s_yoc = (dps / cost * 100) if cost > 0 else 0.0
        s_yield = (dps / price * 100) if price > 0 else 0.0
        
        rows.append({
            t('symbol'): sym,
            t('my_shares'): f"{shares:,.0f}",
            t('avg_cost'): f"₫{cost:,.0f}",
            t('dt_ttm_dps'): f"₫{dps:,.0f}",
            t('dt_yoc'): f"{s_yoc:.2f}%",
            t('dt_yield'): f"{s_yield:.2f}%",
            t('dt_annual_total'): f"₫{inc:,.0f}"
        })

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
else:
    st.info(t("no_data"))
