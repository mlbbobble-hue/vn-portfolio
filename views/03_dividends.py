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
from portfolio import apply_stock_dividend, compute_holdings, compute_received_dividends

st.set_page_config(page_title=f"VN Portfolio | {t('dividends_title')}", page_icon="💰", layout="wide")
from theme import load_css
load_css()

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
        html_str = '<div class="timeline-container">'
        
        # 按照除權息日降冪排序
        if not all_divs.empty:
            timeline_divs = all_divs.sort_values(by="ex_date", ascending=False).copy()
        else:
            timeline_divs = pd.DataFrame()
            
        for _, row in timeline_divs.iterrows():
            sym = row["symbol"]
            dtype = t("cash_div") if row["type"] == "CASH" else t("stock_div")
            ex_date = row.get("ex_date", "N/A")
            pay_date = row.get("pay_date", "")
            pay_str = pay_date if pd.notnull(pay_date) and str(pay_date).strip() else "未定"
            
            # 狀態判斷
            is_done = False
            if row["type"] == "STOCK":
                is_done = (row.get("is_applied", 0) == 1)
            else:
                if pay_date and pd.notnull(pay_date) and str(pay_date).strip():
                    try:
                        is_done = pd.to_datetime(pay_date).date() <= date.today()
                    except:
                        is_done = False
                else:
                    is_done = False

            if is_done:
                status_badge = '<span class="badge-status-done">已發放</span>'
            else:
                status_badge = '<span class="badge-status-pending">在途 / 處理中</span>'
                
            amount_str = f"+{row['cash_amount']:,.0f} VNĐ" if row["type"] == "CASH" else f"+{row['stock_ratio']*100:.1f}% 配股"
            
            html_str += f'''
            <div class="timeline-item">
                <div class="timeline-node"></div>
                <div class="timeline-content">
                    <div class="tl-left">
                        <span class="tl-symbol">{sym}</span>
                        <span class="tl-type">{dtype}</span>
                    </div>
                    <div class="tl-middle">
                        <span>📅 除權息日：{ex_date}</span>
                        <span>💰 實際發放日：{pay_str}</span>
                    </div>
                    <div class="tl-right">
                        {status_badge}
                        <span class="tl-amount">{amount_str}</span>
                    </div>
                </div>
            </div>
            '''
        
        if timeline_divs.empty:
            html_str += '<div style="color:var(--text-muted); text-align:center; padding: 20px;">尚無任何配息紀錄</div>'
            
        html_str += "</div>"
        
        st.markdown(html_str, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 歷史實際獲得配息/配股統計")
        st.markdown("<span style='color:var(--text-muted);font-size:0.9em;'>此統計會比對您的歷史交易紀錄，只有在除息日（Ex-Date）之前持有的股數才會納入配息計算。</span><br><br>", unsafe_allow_html=True)
        
        total_cash_rec, stock_rec_dict, details = compute_received_dividends()
        
        if details:
            # 建立彙整表格
            summary_rows = []
            for sym in set([d['symbol'] for d in details]):
                sym_details = [d for d in details if d['symbol'] == sym]
                sym_cash = sum(d['cash_received'] for d in sym_details)
                sym_stock = stock_rec_dict.get(sym, 0.0)
                if sym_cash > 0 or sym_stock > 0:
                    summary_rows.append({
                        "股票代號": sym,
                        "獲得現金 (VNĐ)": f"{sym_cash:,.0f}",
                        "獲得配股 (股)": f"{sym_stock:,.0f}" if sym_stock > 0 else "-"
                    })
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
            
            # 總和顯示
            total_stock_str = " | ".join([f"{k}: {v:,.0f}股" for k, v in stock_rec_dict.items() if v > 0])
            st.markdown(f"""
            <div style='background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);border-radius:12px;padding:14px 18px;margin-top:8px;'>
                <div style='font-size:1.1em;'>💰 <b>歷史累計獲得現金配息：</b> <span style='color:var(--cathay-green);font-size:1.3em;font-weight:700;'>{total_cash_rec:,.0f} VNĐ</span></div>
                <div style='font-size:1.0em;margin-top:8px;'>📦 <b>歷史累計獲得股票配股：</b> <span style='color:#f59e0b;font-weight:600;'>{total_stock_str if total_stock_str else "無"}</span></div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("目前還沒有實際領到配息的紀錄（可能是剛買入還沒遇到除息日）。")

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
