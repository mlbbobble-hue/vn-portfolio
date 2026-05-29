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
        st.subheader("📊 歷史實際獲得配息/配股統計")
        
        # 1. 取得實際領取的配息資訊
        _, stock_rec_dict, details = compute_received_dividends()
        
        # 2. 合併系統除權息表與使用者實際領取紀錄
        if details:
            details_df = pd.DataFrame(details)
            merged_divs = pd.merge(all_divs, details_df, on=["symbol", "ex_date", "type"], how="inner")
        else:
            merged_divs = pd.DataFrame()
            
        # 3. 計算 Dividend Summary Cards 數據
        this_year = date.today().year
        total_received_this_year = 0.0
        total_pending = 0.0
        total_received_all_time = 0.0
        
        if not merged_divs.empty:
            merged_divs["ex_year"] = pd.to_datetime(merged_divs["ex_date"], errors="coerce").dt.year
            for _, row in merged_divs.iterrows():
                if row["type"] == "CASH":
                    amt = row.get("cash_received", 0)
                    pay_date = row.get("pay_date", "")
                    
                    is_done = False
                    p_year = 0
                    if pay_date and pd.notnull(pay_date) and str(pay_date).strip():
                        try:
                            pdt = pd.to_datetime(pay_date).date()
                            is_done = pdt <= date.today()
                            p_year = pdt.year
                        except:
                            pass
                            
                    if is_done:
                        total_received_all_time += amt
                        if p_year == this_year:
                            total_received_this_year += amt
                    else:
                        total_pending += amt

        # 4. 渲染 Summary Cards
        st.markdown(f"""
<div style="display: flex; gap: 16px; margin-bottom: 24px;">
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">今年已領股利總額</div>
        <div style="color: #10b981; font-size: 24px; font-weight: 700;">+{total_received_this_year:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">在途待領股利總額</div>
        <div style="color: #fbbf24; font-size: 24px; font-weight: 700;">+{total_pending:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">歷年累計總股利</div>
        <div style="color: #f8fafc; font-size: 24px; font-weight: 700;">+{total_received_all_time:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

        # 5. 渲染 Filter Tabs
        years = []
        if not merged_divs.empty:
            years = sorted(merged_divs["ex_year"].dropna().unique().astype(int).tolist(), reverse=True)
            
        tabs_list = ["全部"] + [f"{y}年" for y in years] + ["按個股聚合"]
        tabs = st.tabs(tabs_list)
        
        for i, tab in enumerate(tabs):
            with tab:
                selection = tabs_list[i]
                
                if selection == "全部":
                    filtered_df = merged_divs
                elif selection == "按個股聚合":
                    filtered_df = merged_divs
                else:
                    y_str = selection.replace("年", "")
                    filtered_df = merged_divs[merged_divs["ex_year"] == int(y_str)]
                    
                if selection == "按個股聚合":
                    # --- 渲染手風琴聚合列表 ---
                    if filtered_df.empty:
                        st.markdown('<div style="color:var(--text-muted); text-align:center; padding: 20px;">尚無任何配息紀錄</div>', unsafe_allow_html=True)
                    else:
                        acc_html = '<div class="acc-table" style="max-height: 400px; overflow-y: auto;">'
                        acc_html += """
<div class="acc-header" style="grid-template-columns: 1.5fr 1fr 1fr;">
    <div class="acc-col-left">股票代碼</div>
    <div class="acc-col-right">累計現金配息</div>
    <div class="acc-col-right">累計股票配股</div>
</div>
"""
                        symbols = sorted(filtered_df["symbol"].unique().tolist())
                        for sym in symbols:
                            sym_df = filtered_df[filtered_df["symbol"] == sym].sort_values(by="ex_date", ascending=False)
                            t_cash = sym_df[sym_df["type"] == "CASH"]["cash_received"].sum()
                            t_stock = sym_df[sym_df["type"] == "STOCK"]["stock_received"].sum()
                            
                            c_str = f"+{t_cash:,.0f} VNĐ" if t_cash > 0 else "-"
                            s_str = f"+{t_stock:,.0f} 股" if t_stock > 0 else "-"
                            
                            acc_html += f"""
<details class="acc-details">
    <summary>
        <div class="acc-row" style="grid-template-columns: 1.5fr 1fr 1fr;">
            <div class="acc-col-left">
                <span class="tlt-main"><span class="acc-arrow">▶</span>{sym}</span>
                <span class="tlt-sub" style="margin-left: 16px;">共 {len(sym_df)} 筆紀錄</span>
            </div>
            <div class="acc-col-right">
                <span class="tlt-main" style="color: #10b981;">{c_str}</span>
            </div>
            <div class="acc-col-right">
                <span class="tlt-main" style="color: #f59e0b;">{s_str}</span>
            </div>
        </div>
    </summary>"""
                            for _, r in sym_df.iterrows():
                                e_date = r.get("ex_date", "N/A")
                                dtype = t("cash_div") if r["type"] == "CASH" else t("stock_div")
                                if r["type"] == "CASH":
                                    a_str = f"+{r.get('cash_received', 0):,.0f} VNĐ"
                                else:
                                    a_str = f"+{r.get('stock_received', 0):,.0f} 股"
                                    
                                acc_html += f"""
<div class="acc-sub-row" style="grid-template-columns: 1.5fr 1fr 1fr;">
    <div class="acc-col-left">
        <span class="tlt-main" style="font-size:15px; color:#cbd5e1;">└ {e_date}</span>
        <span class="tlt-sub" style="margin-left: 18px;">{dtype}</span>
    </div>
    <div class="acc-col-right">
        <span class="tlt-main" style="font-size:15px; color:#10b981;">{a_str if r['type'] == 'CASH' else '-'}</span>
    </div>
    <div class="acc-col-right">
        <span class="tlt-main" style="font-size:15px; color:#f59e0b;">{a_str if r['type'] == 'STOCK' else '-'}</span>
    </div>
</div>"""
                            acc_html += "</details>"
                        acc_html += "</div>"
                        st.markdown(acc_html, unsafe_allow_html=True)
                        
                else:
                    # --- 渲染一般 Timeline ---
                    html_str = '<div class="timeline-container" style="max-height: 400px; overflow-y: auto;">'
                    if not filtered_df.empty:
                        timeline_divs = filtered_df.sort_values(by="ex_date", ascending=False)
                        for _, row in timeline_divs.iterrows():
                            sym = row["symbol"]
                            dtype = t("cash_div") if row["type"] == "CASH" else t("stock_div")
                            ex_date = row.get("ex_date", "N/A")
                            pay_date = row.get("pay_date", "")
                            pay_str = pay_date if pd.notnull(pay_date) and str(pay_date).strip() else "未定"
                            
                            is_done = False
                            if row["type"] == "STOCK":
                                is_done = (row.get("is_applied", 0) == 1)
                            else:
                                if pay_date and pd.notnull(pay_date) and str(pay_date).strip():
                                    try:
                                        is_done = pd.to_datetime(pay_date).date() <= date.today()
                                    except:
                                        is_done = False

                            if is_done:
                                status_badge = '<span class="badge-status-done">已發放</span>'
                            else:
                                status_badge = '<span class="badge-status-pending">在途 / 處理中</span>'
                                
                            if row["type"] == "CASH":
                                amount_str = f"+{row.get('cash_received', 0):,.0f} VNĐ"
                            else:
                                amount_str = f"+{row.get('stock_received', 0):,.0f} 股"
                            
                            html_str += f"""
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
</div>"""
                    else:
                        html_str += '<div style="color:var(--text-muted); text-align:center; padding: 20px;">尚無任何配息紀錄</div>'
                    html_str += "</div>"
                    st.markdown(html_str, unsafe_allow_html=True)

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
