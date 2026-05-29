"""頁面3：配息追蹤（雙語 + db_router）"""
import streamlit as st
import pandas as pd
from datetime import date
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (add_dividend_event, get_dividend_events, delete_dividend_event,
                        mark_dividend_applied, upsert_dividend_events_bulk,
                        get_portfolio_symbols, add_transaction)
from market_data import get_dividend_history
from portfolio import apply_stock_dividend, compute_holdings

st.set_page_config(page_title=f"VN Portfolio | {t('dividends_title')}", page_icon="💰", layout="wide")
from theme import load_css
load_css()

with st.sidebar:
    render_lang_switcher()
    st.divider()
    render_user_info_sidebar()

if not check_auth():
    st.stop()

st.markdown(f"""
<div class="page-header">
    <h2>{t('dividends_title')}</h2>
    <p>{t('dividends_desc')}</p>
</div>""", unsafe_allow_html=True)

tab_ov, tab_auto, tab_man, tab_apply = st.tabs([
    t("tab_overview"), t("tab_auto_fetch"), t("tab_manual"), t("tab_apply_stock")
])

# ── Tab 1: 總覽 ─────────────────────────────────────────────
with tab_ov:
    all_divs = get_dividend_events()
    holdings = compute_holdings()
    if all_divs.empty:
        st.info(t("no_data"))
    else:
        st.subheader(t("upcoming_exdate"))
        today = date.today()
        upcoming = all_divs[all_divs["ex_date"] != ""].copy()
        upcoming["ex_date_dt"] = pd.to_datetime(upcoming["ex_date"], errors="coerce")
        upcoming = upcoming.dropna(subset=["ex_date_dt"])
        upcoming["days_left"] = (upcoming["ex_date_dt"].dt.date - today).apply(lambda x: x.days)
        soon = upcoming[(upcoming["days_left"] >= 0) & (upcoming["days_left"] <= 60)].sort_values("days_left")
        if soon.empty:
            st.info(t("no_upcoming"))
        else:
            for _, row in soon.iterrows():
                icon = "🔴" if row["days_left"] <= 7 else "🟡" if row["days_left"] <= 30 else "🟢"
                dtype_str = t("cash_div") if row["type"]=="CASH" else t("stock_div")
                amount_str = (f"{row['cash_amount']:,.0f} {t('cash_per_share')}" if row["type"]=="CASH"
                              else f"{t('stock_ratio_label')}: {row['stock_ratio']*100:.1f}%")
                st.markdown(f"""
                <div class="ex-soon">
                    {icon} <b>{row['symbol']}</b> — {dtype_str} | {t('ex_date')}: {row['ex_date']}
                    <span style='color:var(--text-muted);'> ({t('days_left', n=int(row['days_left']))})</span>
                    <br><span style='color:#fbbf24;margin-left:24px;'>{amount_str}</span>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader(t("all_div_records"))
        # Select and rename only the columns we want (avoid duplicate names)
        cols_to_show = ["id","symbol","ex_date","pay_date","type",
                        "cash_amount","stock_ratio","is_applied","source"]
        cols_exist = [c for c in cols_to_show if c in all_divs.columns]
        disp = all_divs[cols_exist].rename(columns={
            "id":"#", "symbol":t("symbol"), "ex_date":t("ex_date"),
            "pay_date":t("pay_date"), "type":"Type",
            "cash_amount":t("cash_div"), "stock_ratio":t("stock_ratio_label"),
            "is_applied":t("applied"), "source":"Source",
        })
        st.dataframe(disp, use_container_width=True, height=300)

        st.markdown("---")
        st.subheader(t("annual_income_title"))
        if not holdings.empty:
            shares_map = holdings.set_index("symbol")["total_shares"].to_dict()
            cash_divs  = all_divs[all_divs["type"]=="CASH"]
            rows_inc = []
            for sym, s in shares_map.items():
                dps = cash_divs[cash_divs["symbol"]==sym]["cash_amount"].sum()
                rows_inc.append({t("symbol"):sym, t("my_shares"):f"{s:,.0f}",
                                 t("annual_dps"):f"{dps:,.0f}", t("est_income"):f"{dps*s:,.0f}"})
            st.dataframe(pd.DataFrame(rows_inc), use_container_width=True)
            total_income = sum(cash_divs[cash_divs["symbol"]==s]["cash_amount"].sum()*sh
                               for s,sh in shares_map.items())
            st.markdown(f"""
            <div style='background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);border-radius:12px;padding:14px 18px;margin-top:8px;'>
                {t('total_annual_income', val=f"{total_income:,.0f}")}
            </div>""", unsafe_allow_html=True)

# ── Tab 2: 自動抓取 ─────────────────────────────────────────
with tab_auto:
    st.subheader(t("auto_fetch_title"))
    my_syms = get_portfolio_symbols()
    if not my_syms:
        st.warning(t("no_data"))
    else:
        st.markdown(f"{t('my_holdings')} {', '.join([f'`{s}`' for s in my_syms])}")
        extra = st.text_input(t("extra_symbols"), placeholder="VNM,MWG")
        all_t = my_syms.copy()
        if extra: all_t += [s.strip().upper() for s in extra.split(",") if s.strip()]
        if st.button(t("start_fetch"), use_container_width=True):
            prog = st.progress(0); status = st.empty()
            for i, sym in enumerate(all_t):
                status.text(f"{sym}...")
                try:
                    divs = get_dividend_history(sym)
                    if divs:
                        upsert_dividend_events_bulk(divs)
                        st.write(t("fetch_result_ok", sym=sym, n=len(divs)))
                    else:
                        st.write(t("fetch_result_none", sym=sym))
                except Exception as e:
                    st.write(t("fetch_result_err", sym=sym, err=e))
                prog.progress((i+1)/len(all_t))
            status.empty()
            st.success(t("fetch_complete"))

# ── Tab 3: 手動 ─────────────────────────────────────────────
with tab_man:
    st.subheader(t("add_div_title"))
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        m_sym    = st.text_input(t("symbol"), key="m_sym").upper()
        m_type   = st.radio(t("div_type"), [t("cash_div"), t("stock_div")], horizontal=True, key="m_type")
        m_exdate = st.date_input(t("ex_date"), value=date.today(), key="m_ex")
    with c2:
        m_pay    = st.date_input(t("pay_date"), value=date.today(), key="m_pay")
        if t("cash_div") in m_type:
            m_cash  = st.number_input(t("cash_per_share"), min_value=0, step=100, value=2000, key="m_cash")
            m_ratio = 0.0
        else:
            m_ratio = st.number_input(t("stock_ratio_label")+" (0.15=15%)", min_value=0.0, max_value=1.0,
                                      step=0.01, value=0.10, format="%.2f", key="m_ratio")
            m_cash  = 0.0
    dtype = "CASH" if t("cash_div") in m_type else "STOCK"
    if st.button(t("add_div_btn"), use_container_width=True):
        if not m_sym:
            st.error(t("enter_symbol"))
        else:
            add_dividend_event(m_sym, str(m_exdate), str(m_pay), dtype, m_cash, m_ratio, "manual")
            st.success(t("div_added_ok", sym=m_sym))
            st.rerun()
    st.markdown("---")
    st.subheader(t("delete_div_title"))
    del_id = st.number_input(t("delete_div_hint"), min_value=1, step=1, key="del_div")
    if st.button("❌ "+t("delete"), key="del_div_btn"):
        delete_dividend_event(int(del_id))
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 4: 套用 ─────────────────────────────────────────────
with tab_apply:
    st.subheader(t("apply_stock_title"))
    st.markdown(t("apply_stock_desc"))
    all_divs_a = get_dividend_events()
    pending = all_divs_a[(all_divs_a["type"]=="STOCK") & (all_divs_a["is_applied"]==0)] if not all_divs_a.empty else pd.DataFrame()
    if pending.empty:
        st.info(t("no_pending_stock"))
    else:
        st.warning(t("pending_stock_warn", n=len(pending)))
        for _, row in pending.iterrows():
            with st.expander(f"📦 {row['symbol']} — {row['stock_ratio']*100:.1f}% | {row['ex_date']}"):
                preview = apply_stock_dividend(row["symbol"], row["stock_ratio"])
                if preview:
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric(t("old_shares"), f"{preview['old_shares']:,.0f}")
                    with c2: st.metric(t("new_shares"), f"{preview['new_shares']:,.0f}",
                                       delta=f"+{preview['new_shares']-preview['old_shares']:,.0f}")
                    with c3: st.metric(t("new_avg_cost"), f"{preview['new_avg_cost']:,.0f}",
                                       delta=f"{preview['new_avg_cost']-preview['old_avg_cost']:,.0f}")
                    if st.button(t("apply_btn", sym=row["symbol"]), key=f"apply_{row['id']}"):
                        new_cnt = preview["new_shares"] - preview["old_shares"]
                        add_transaction(str(row.get("pay_date",row.get("ex_date",""))),
                                        "股利發放","BUY" if True else "BUY",
                                        row["symbol"],"BUY",new_cnt,0,0,"股票股利自動套用")
                        mark_dividend_applied(int(row["id"]))
                        st.success(t("apply_ok", sym=row["symbol"], n=new_cnt))
                        st.rerun()
                else:
                    st.warning(t("no_holdings_for", sym=row["symbol"]))
