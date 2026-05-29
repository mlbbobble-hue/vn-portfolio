"""
app.py — 主程式（首頁 Dashboard）
雙語 🇻🇳🇹🇼 + Supabase Auth + 響應式深色介面
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (seed_test_data, get_portfolio_symbols,
                        upsert_price_cache, get_watchlist)
from portfolio import compute_portfolio_with_prices
from db_router import get_price_cache
from market_data import get_multiple_prices
from alerts import check_and_fire_alerts
from config import PRICE_REFRESH_SECONDS

# ── 頁面設定 ───────────────────────────────────────────────────
st.set_page_config(
    page_title="VN Portfolio | 越南股市投資組合",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全域樣式 ───────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp {
      background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
      color: #e2e8f0;
  }
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #1e1e3a 0%, #16213e 100%);
      border-right: 1px solid rgba(99,102,241,0.2);
  }
  .metric-card {
      background: linear-gradient(135deg, rgba(30,30,60,0.8), rgba(20,20,45,0.9));
      border: 1px solid rgba(99,102,241,0.3);
      border-radius: 16px; padding: 20px 24px; margin: 6px 0;
      backdrop-filter: blur(10px);
      transition: all 0.3s ease;
  }
  .metric-card:hover { border-color: rgba(99,102,241,0.7); box-shadow: 0 4px 20px rgba(99,102,241,0.2); }
  .metric-value { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
  .metric-label { font-size: 0.82rem; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 4px; }
  .metric-sub { font-size: 0.85rem; color: #64748b; margin-top: 2px; }
  .positive { color: #34d399 !important; }
  .negative { color: #f87171 !important; }
  .page-header {
      background: linear-gradient(90deg, rgba(99,102,241,0.15) 0%, transparent 100%);
      border-left: 4px solid #6366f1;
      padding: 12px 20px; border-radius: 0 12px 12px 0; margin-bottom: 24px;
  }
  .stButton > button {
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: white; border: none; border-radius: 8px; font-weight: 500;
      transition: all 0.2s;
  }
  .stButton > button:hover {
      box-shadow: 0 4px 15px rgba(99,102,241,0.4); transform: translateY(-1px);
  }
  .stButton > button[kind="secondary"] {
      background: transparent !important;
      border: 1px solid rgba(99,102,241,0.4) !important;
      color: #a78bfa !important;
  }
  .alert-banner {
      background: linear-gradient(135deg, rgba(251,191,36,0.15), rgba(245,158,11,0.1));
      border: 1px solid rgba(251,191,36,0.4);
      border-radius: 12px; padding: 12px 16px; margin: 8px 0;
  }
  [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
  .stTabs [data-baseweb="tab-list"] { background: rgba(30,30,60,0.5); border-radius: 10px; padding: 4px; }
  .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #94a3b8; }
  .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; }
  hr { border-color: rgba(99,102,241,0.2) !important; }
</style>
""", unsafe_allow_html=True)

# ── 驗證登入 ───────────────────────────────────────────────────
if not check_auth():
    st.stop()


def fmt_vnd(v): 
    if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.2f} tỷ"
    if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M"
    return f"{v:,.0f}"

def fmt_pct(v):
    return f"{'▲' if v>0 else '▼' if v<0 else '─'} {abs(v):.2f}%"


# ── 側邊欄 ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:12px 0;'>
        <div style='font-size:2.5rem'>📈</div>
        <div style='font-size:1.05rem; font-weight:700; color:#a78bfa;'>VN Portfolio</div>
        <div style='font-size:0.75rem; color:#64748b;'>{t('app_tagline')}</div>
    </div>
    """, unsafe_allow_html=True)

    render_lang_switcher()
    st.divider()
    render_user_info_sidebar()
    st.divider()

    if st.button(t("update_price"), use_container_width=True):
        with st.spinner(t("updating")):
            symbols = get_portfolio_symbols()
            wl_syms = []
            try:
                wl_df = get_watchlist()
                if not wl_df.empty:
                    wl_syms = wl_df["symbol"].tolist()
            except Exception:
                pass
            all_syms = list(set(symbols + wl_syms))
            if all_syms:
                prices_df = get_multiple_prices(all_syms)
                for _, p in prices_df.iterrows():
                    upsert_price_cache(p["symbol"], p["price"], p["change_pct"], p.get("volume", 0))
                st.success(t("updated_count", n=len(all_syms)))
                st.rerun()

    st.divider()

    # 提醒狀態
    try:
        fired = check_and_fire_alerts()
        if fired:
            st.markdown(f"""
            <div class="alert-banner">
                ⚠️ <b>{len(fired)} {t('warning')}</b>
                {"".join(f"<br>• {a['symbol']} @ {a['price']:,.0f}" for a in fired)}
            </div>""", unsafe_allow_html=True)
    except Exception:
        pass

    st.markdown(f"""
    <div style='position:fixed;bottom:20px;left:16px;right:16px;font-size:0.72rem;
                color:#475569;text-align:center;'>
        {t('disclaimer')}<br>{t('data_source')}
    </div>""", unsafe_allow_html=True)


# ── 主頁面 ─────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
    <h1>{t('dashboard_title')}</h1>
    <p>{t('dashboard_desc')}</p>
</div>
""", unsafe_allow_html=True)

seed_test_data()

# 計算持倉
from portfolio import compute_holdings
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

    # KPI 卡片
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

    # 快速一覽表
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
