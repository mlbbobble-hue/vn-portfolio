"""頁面5：損益分析（雙語 + db_router）"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import get_all_transactions, get_dividend_events
from portfolio import compute_portfolio_with_prices, compute_holdings
from market_data import get_historical_prices

st.set_page_config(page_title=f"VN Portfolio | {t('analytics_title')}", page_icon="📉", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);color:#e2e8f0;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1e1e3a 0%,#16213e 100%);border-right:1px solid rgba(99,102,241,0.2);}
.stButton>button{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border:none;border-radius:8px;font-weight:500;}
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
    <h2 style='margin:0;color:#e2e8f0;'>{t('analytics_title')}</h2>
    <p style='margin:4px 0 0;color:#94a3b8;font-size:0.9rem;'>{t('analytics_desc')}</p>
</div>""", unsafe_allow_html=True)

tab_div, tab_pl, tab_hist = st.tabs([t("tab_monthly_div"), t("tab_pl_contrib"), t("tab_price_hist")])

# ── Tab 1: 月度股利 ─────────────────────────────────────────
with tab_div:
    st.subheader(t("monthly_div_title"))
    all_divs = get_dividend_events()
    holdings = compute_holdings()
    if all_divs.empty or holdings.empty:
        st.info(t("no_data"))
    else:
        shares_map = holdings.set_index("symbol")["total_shares"].to_dict()
        cash_divs  = all_divs[all_divs["type"]=="CASH"].copy()
        cash_divs["pay_date_dt"] = pd.to_datetime(cash_divs["pay_date"], errors="coerce")
        cash_divs = cash_divs.dropna(subset=["pay_date_dt"])
        cash_divs["year_month"] = cash_divs["pay_date_dt"].dt.to_period("M").astype(str)
        inc_rows = []
        for _, row in cash_divs.iterrows():
            sym = row["symbol"]; my_s = shares_map.get(sym, 0)
            inc_rows.append({"year_month": row["year_month"], "symbol": sym, "income": row["cash_amount"]*my_s})
        if inc_rows:
            inc_df  = pd.DataFrame(inc_rows)
            monthly = inc_df.groupby("year_month")["income"].sum().reset_index().sort_values("year_month")
            fig = go.Figure(go.Bar(
                x=monthly["year_month"], y=monthly["income"]/1_000_000,
                marker=dict(color=monthly["income"], colorscale="Viridis"),
                text=[f"{v/1_000_000:.1f}M" for v in monthly["income"]], textposition="outside",
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#e2e8f0"), height=380,
                              xaxis=dict(gridcolor="rgba(99,102,241,0.1)", title=t("month_axis")),
                              yaxis=dict(gridcolor="rgba(99,102,241,0.1)", title=t("monthly_div_axis")),
                              margin=dict(t=20,b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader(t("by_stock_div"))
            sym_total = inc_df.groupby("symbol")["income"].sum().reset_index()
            fig2 = px.pie(sym_total, values="income", names="symbol", hole=0.5,
                          color_discrete_sequence=px.colors.sequential.Viridis)
            fig2.update_traces(textinfo="label+percent", textposition="outside")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                               height=320, margin=dict(t=10,b=10), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            total = inc_df["income"].sum()
            st.markdown(f"""
            <div style='background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);border-radius:12px;padding:14px 18px;'>
                {t('cumulative_income', val=f"{total:,.0f}", m=f"{total/1_000_000:.1f}")}
            </div>""", unsafe_allow_html=True)
        else:
            st.info(t("no_income_data"))

# ── Tab 2: 損益貢獻 ─────────────────────────────────────────
with tab_pl:
    st.subheader(t("pl_by_stock_title"))
    portfolio_df = compute_portfolio_with_prices()
    if portfolio_df.empty:
        st.info(t("no_holdings_chart"))
    else:
        has_price = portfolio_df[portfolio_df["current_price"]>0].copy()
        if not has_price.empty:
            sorted_df = has_price.sort_values("unrealized_pl", ascending=False)
            fig = go.Figure(go.Bar(
                x=sorted_df["symbol"], y=sorted_df["unrealized_pl"]/1_000_000,
                marker_color=["#34d399" if v>=0 else "#f87171" for v in sorted_df["unrealized_pl"]],
                text=[f"{v/1_000_000:+.2f}M\n({r:+.1f}%)" for v,r in zip(sorted_df["unrealized_pl"],sorted_df["roi_pct"])],
                textposition="outside",
            ))
            fig.update_layout(title=t("unrealized_pl_chart"), paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                              xaxis=dict(gridcolor="rgba(99,102,241,0.1)"),
                              yaxis=dict(gridcolor="rgba(99,102,241,0.1)", title="M VNĐ"),
                              height=360, margin=dict(t=40,b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(name=t("invested_cost"), x=has_price["symbol"],
                                  y=has_price["total_cost"]/1_000_000, marker_color="rgba(99,102,241,0.6)"))
            fig3.add_trace(go.Bar(name=t("current_value"), x=has_price["symbol"],
                                  y=has_price["market_value"]/1_000_000, marker_color="rgba(52,211,153,0.7)"))
            fig3.update_layout(title=t("cost_vs_value"), barmode="group",
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font=dict(color="#e2e8f0"),
                               xaxis=dict(gridcolor="rgba(99,102,241,0.1)"),
                               yaxis=dict(gridcolor="rgba(99,102,241,0.1)", title="M VNĐ"),
                               height=340, margin=dict(t=40,b=20), legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning(t("no_price_yet"))
            cost_df = portfolio_df.copy()
            fig_c = px.bar(cost_df, x="symbol", y="total_cost", title=t("cost_dist"),
                           color="symbol", color_discrete_sequence=px.colors.sequential.Plasma_r)
            fig_c.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#e2e8f0"), height=320)
            st.plotly_chart(fig_c, use_container_width=True)

# ── Tab 3: 歷史走勢 ─────────────────────────────────────────
with tab_hist:
    st.subheader(t("hist_title"))
    holdings = compute_holdings()
    if holdings.empty:
        st.info(t("no_holdings_chart"))
        st.stop()
    sym_options = holdings["symbol"].tolist()
    sel_sym = st.selectbox(t("select_stock"), sym_options, key="hist_sym")
    days    = st.slider(t("days_label"), min_value=30, max_value=730, value=365, step=30, key="hist_days")
    if st.button(t("load_hist_btn"), use_container_width=True, key="load_hist"):
        with st.spinner(t("fetching_hist", sym=sel_sym, n=days)):
            hist_df = get_historical_prices(sel_sym, days)
        if hist_df.empty:
            st.error(t("no_hist_data"))
        else:
            close_col = next((c for c in hist_df.columns if c.lower()=="close"), None)
            date_col  = next((c for c in hist_df.columns if c.lower() in ["time","date","tradingdate"]), None)
            if close_col and date_col:
                hist_df["MA20"] = hist_df[close_col].rolling(20).mean()
                hist_df["MA60"] = hist_df[close_col].rolling(60).mean()
                fig_h = go.Figure()
                fig_h.add_trace(go.Scatter(x=hist_df[date_col], y=hist_df[close_col], mode="lines",
                    name=t("close_price"), line=dict(color="#a78bfa",width=2),
                    fill="tozeroy", fillcolor="rgba(99,102,241,0.08)"))
                fig_h.add_trace(go.Scatter(x=hist_df[date_col], y=hist_df["MA20"], mode="lines",
                    name=t("ma20"), line=dict(color="#fbbf24",width=1.5,dash="dot")))
                fig_h.add_trace(go.Scatter(x=hist_df[date_col], y=hist_df["MA60"], mode="lines",
                    name=t("ma60_line"), line=dict(color="#f97316",width=1.5,dash="dash")))
                txns = get_all_transactions()
                for action, color, symbol_marker, label in [
                    ("BUY","#34d399","triangle-up",t("buy_point")),
                    ("SELL","#f87171","triangle-down",t("sell_point")),
                ]:
                    sub = txns[(txns["symbol"]==sel_sym)&(txns["action"]==action)]
                    if not sub.empty:
                        fig_h.add_trace(go.Scatter(x=sub["date"], y=sub["price"], mode="markers",
                            name=label, marker=dict(color=color,size=10,symbol=symbol_marker,
                            line=dict(color="white",width=1.5))))
                sym_divs = get_dividend_events(sel_sym)
                for ed in (sym_divs[sym_divs["ex_date"]!=""]["ex_date"].tolist() if not sym_divs.empty else []):
                    fig_h.add_vline(x=ed, line=dict(color="rgba(251,191,36,0.4)",dash="dash",width=1),
                        annotation_text=t("ex_date_mark"), annotation_font_color="#fbbf24", annotation_font_size=10)
                fig_h.update_layout(
                    title=t("hist_chart_title", sym=sel_sym, n=days),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"), height=480,
                    xaxis=dict(gridcolor="rgba(99,102,241,0.1)", rangeslider=dict(visible=True)),
                    yaxis=dict(gridcolor="rgba(99,102,241,0.1)", title="VNĐ"),
                    margin=dict(t=40,b=20),
                    legend=dict(bgcolor="rgba(0,0,0,0)",orientation="h",yanchor="bottom",y=1.02),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.error(t("col_format_error"))
