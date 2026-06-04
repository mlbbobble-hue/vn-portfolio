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

tab_ov, tab_lookup, tab_auto, tab_man, tab_apply = st.tabs([
    t("tab_overview"), t("tab_lookup"), t("tab_auto_fetch"), t("tab_manual"), t("tab_apply_stock")
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
        st.subheader(t("div_hist_stats_title"))
        
        # 1. 取得實際領取的配息資訊
        _, stock_rec_dict, details = compute_received_dividends()
        
        # 2. 合併系統除權息表與使用者實際領取紀錄
        if details:
            details_df = pd.DataFrame(details)
            merged_divs = pd.merge(all_divs, details_df, on=["symbol", "ex_date", "type"], how="inner")
        else:
            merged_divs = pd.DataFrame()
            
        # 3. 計算 Dividend Summary Cards 數據
        from db_router import get_price_cache
        price_cache_df = get_price_cache()
        price_cache = price_cache_df.set_index("symbol")["price"].to_dict() if not price_cache_df.empty else {}

        this_year = date.today().year
        
        # Cash Div
        total_received_this_year = 0.0
        total_pending = 0.0
        total_received_all_time = 0.0
        
        # Stock Div (Current Value)
        total_stock_val_this_year = 0.0
        total_pending_stock_val = 0.0
        total_stock_val_all_time = 0.0
        
        if not merged_divs.empty:
            merged_divs["ex_year"] = pd.to_datetime(merged_divs["ex_date"], errors="coerce").dt.year
            for _, row in merged_divs.iterrows():
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
                        
                if row["type"] == "CASH":
                    amt = row.get("cash_received", 0)
                    if is_done:
                        total_received_all_time += amt
                        if p_year == this_year:
                            total_received_this_year += amt
                    else:
                        total_pending += amt
                elif row["type"] == "STOCK":
                    shares_amt = row.get("stock_received", 0)
                    sym = row["symbol"]
                    current_price = price_cache.get(sym, 0)
                    stock_val = shares_amt * current_price
                    
                    if is_done:
                        total_stock_val_all_time += stock_val
                        if p_year == this_year:
                            total_stock_val_this_year += stock_val
                    else:
                        total_pending_stock_val += stock_val

        # 4. 渲染 Summary Cards
        st.markdown(f"""
<div style="display: flex; gap: 16px; margin-bottom: 16px;">
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(16, 185, 129, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #10b981;">
        <div style="color: #00F0FF; font-size: 13px; margin-bottom: 8px;">💰 今年累計領取配息 (Cash Div)</div>
        <div style="color: #00FF41; font-size: 24px; font-weight: 700;">+{total_received_this_year:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(251, 191, 36, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #fbbf24;">
        <div style="color: #00F0FF; font-size: 13px; margin-bottom: 8px;">⏳ 即將入帳配息 (Pending Cash)</div>
        <div style="color: #fbbf24; font-size: 24px; font-weight: 700;">+{total_pending:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(248, 250, 252, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #f8fafc;">
        <div style="color: #00F0FF; font-size: 13px; margin-bottom: 8px;">📈 歷史累計配息 (All-time Cash)</div>
        <div style="color: #f8fafc; font-size: 24px; font-weight: 700;">+{total_received_all_time:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
</div>
<div style="display: flex; gap: 16px; margin-bottom: 24px;">
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #3b82f6;">
        <div style="color: #00F0FF; font-size: 13px; margin-bottom: 8px;">🎁 今年領取配股現值 (Stock Div Value)</div>
        <div style="color: #3b82f6; font-size: 24px; font-weight: 700;">+{total_stock_val_this_year:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(168, 85, 247, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #a855f7;">
        <div style="color: #00F0FF; font-size: 13px; margin-bottom: 8px;">⏳ 即將發放配股現值 (Pending Stock)</div>
        <div style="color: #a855f7; font-size: 24px; font-weight: 700;">+{total_pending_stock_val:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(236, 72, 153, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #ec4899;">
        <div style="color: #00F0FF; font-size: 13px; margin-bottom: 8px;">💎 歷史累計配股現值 (All-time Stock)</div>
        <div style="color: #ec4899; font-size: 24px; font-weight: 700;">+{total_stock_val_all_time:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # --- Cyberpunk Style Bar Chart (CASH ONLY) ---
        df_div_chart = all_divs[all_divs["ex_date"] != ""].copy()
        df_div_chart["ex_date"] = pd.to_datetime(df_div_chart["ex_date"], errors="coerce")
        df_div_chart = df_div_chart.dropna(subset=["ex_date"])
        
        # 依照使用者要求：只看現金配息 (CASH ONLY)
        df_div_chart = df_div_chart[df_div_chart["type"] == "CASH"]
        
        df_div_chart["month"] = df_div_chart["ex_date"].dt.strftime("%Y-%m")
        
        df_div_chart["val"] = 0.0
        
        for idx, r in df_div_chart.iterrows():
            if r["type"] == "CASH":
                df_div_chart.at[idx, "val"] = float(r.get("cash_received", 0))
            else:
                sym = r["symbol"]
                curr_price = price_cache.get(sym, 0)
                df_div_chart.at[idx, "val"] = float(r.get("stock_received", 0)) * curr_price
                
        df_monthly = df_div_chart.groupby(["month", "type"])["val"].sum().reset_index()
        df_monthly["type_str"] = df_monthly["type"].map({"CASH": "現金配息", "STOCK": "配股現值"})
        
        import plotly.express as px
        fig_bar = px.bar(df_monthly, x="month", y="val", color="type_str", 
                         color_discrete_map={"現金配息": "#00F0FF", "配股現值": "#FF007F"},
                         barmode="stack")
        
        lang = st.session_state.get("lang", "zh")
        bar_title = "每月被動收入趨勢" if lang == "zh" else "Xu hướng thu nhập thụ động hàng tháng"
        
        fig_bar.update_layout(
            title=dict(text=f"<b>{bar_title}</b>", font=dict(size=16, color="#E0F7FA")),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20, l=40, r=20),
            height=280,
            yaxis=dict(title="", gridcolor="visible=False", zeroline=False),
            xaxis=dict(title="", gridcolor="rgba(0,0,0,0)", zeroline=False, type='category'),
            legend=dict(title="", orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(color="#E0F7FA"))
        )
        st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 24px;'>", unsafe_allow_html=True)
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 5. 渲染 Filter Tabs
        years = []
        if not merged_divs.empty:
            years = sorted(merged_divs["ex_year"].dropna().unique().astype(int).tolist(), reverse=True)
            
        tabs_list = [t("div_filter_all")] + [t("div_year_filter", y=y) for y in years] + [t("div_filter_group")]
        tabs = st.tabs(tabs_list)
        
        for i, tab in enumerate(tabs):
            with tab:
                selection = tabs_list[i]
                
                if selection == t("div_filter_all"):
                    filtered_df = merged_divs
                elif selection == t("div_filter_group"):
                    filtered_df = merged_divs
                else:
                    target_y = years[i - 1]
                    filtered_df = merged_divs[merged_divs["ex_year"] == int(target_y)]
                    
                if selection == t("div_filter_group"):
                    # --- 渲染手風琴聚合列表 ---
                    if filtered_df.empty:
                        st.markdown(f'<div style="color:var(--text-muted); text-align:center; padding: 20px;">{t("no_records")}</div>', unsafe_allow_html=True)
                    else:
                        acc_html = '<div class="acc-table" style="max-height: 400px; overflow-y: auto;">'
                        acc_html += """
<div class="acc-header" style="grid-template-columns: 1.5fr 1fr 1fr;">
    <div class="acc-col-left">{t("div_sym")}</div>
    <div class="acc-col-right">{t("div_acc_cash_dist")}</div>
    <div class="acc-col-right">{t("div_acc_stock_dist")}</div>
</div>
"""
                        symbols = sorted(filtered_df["symbol"].unique().tolist())
                        for sym in symbols:
                            sym_df = filtered_df[filtered_df["symbol"] == sym].sort_values(by="ex_date", ascending=False)
                            t_cash = sym_df[sym_df["type"] == "CASH"]["cash_received"].sum()
                            t_stock = sym_df[sym_df["type"] == "STOCK"]["stock_received"].sum()
                            
                            c_str = f"+{t_cash:,.0f} VNĐ" if t_cash > 0 else "-"
                            
                            curr_price = price_cache.get(sym, 0)
                            if t_stock > 0:
                                s_str = f"+{t_stock:,.0f} 股"
                                if curr_price > 0:
                                    s_str += f" <span style='font-size:12px; color:#94a3b8;'>(≈ {t_stock * curr_price:,.0f} VNĐ)</span>"
                            else:
                                s_str = "-"
                            
                            acc_html += f"""
<details class="acc-details">
    <summary>
        <div class="acc-row" style="grid-template-columns: 1.5fr 1fr 1fr;">
            <div class="acc-col-left">
                <span class="tlt-main"><span class="acc-arrow">▶</span>{sym}</span>
                <span class="tlt-sub" style="margin-left: 16px;">{t("total_records", n=len(sym_df))}</span>
            </div>
            <div class="acc-col-right">
                <span class="tlt-main" style="color: #00FF41;">{c_str}</span>
            </div>
            <div class="acc-col-right">
                <span class="tlt-main" style="color: #00F0FF;">{s_str}</span>
            </div>
        </div>
    </summary>"""
                            for _, r in sym_df.iterrows():
                                e_date = r.get("ex_date", "N/A")
                                dtype = t("cash_div") if r["type"] == "CASH" else t("stock_div")
                                if r["type"] == "CASH":
                                    a_str = f"+{r.get('cash_received', 0):,.0f} VNĐ"
                                else:
                                    shares_rec = r.get('stock_received', 0)
                                    curr_price = price_cache.get(sym, 0)
                                    a_str = f"+{shares_rec:,.0f} 股"
                                    if curr_price > 0:
                                        a_str += f" <span style='font-size:12px; color:#94a3b8;'>(≈ {shares_rec * curr_price:,.0f} VNĐ)</span>"
                                    
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
                            pay_str = pay_date if pd.notnull(pay_date) and str(pay_date).strip() else t("tba")
                            
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
                                status_badge = f'<span class="badge-status-done">{t("paid_status")}</span>'
                            else:
                                status_badge = f'<span class="badge-status-pending">{t("pending_status")}</span>'
                                
                            if row["type"] == "CASH":
                                amount_str = f"+{row.get('cash_received', 0):,.0f} VNĐ"
                            else:
                                shares_rec = row.get('stock_received', 0)
                                curr_price = price_cache.get(sym, 0)
                                amount_str = f"+{shares_rec:,.0f} {t('div_shares')}"
                                if curr_price > 0:
                                    amount_str += f" <br><span style='font-size:12px; color:#94a3b8;'>(≈ {shares_rec * curr_price:,.0f} VNĐ)</span>"
                            
                            html_str += f"""
<div class="timeline-item">
    <div class="timeline-node"></div>
    <div class="timeline-content">
        <div class="tl-left">
            <span class="tl-symbol">{sym}</span>
            <span class="tl-type">{dtype}</span>
        </div>
        <div class="tl-middle">
            <span>{t("div_ex_date_lbl")}{ex_date}</span>
            <span>{t("div_pay_date_lbl")}{pay_str}</span>
        </div>
        <div class="tl-right">
            {status_badge}
            <span class="tl-amount">{amount_str}</span>
        </div>
    </div>
</div>"""
                    else:
                        html_str += f'<div style="color:var(--text-muted); text-align:center; padding: 20px;">{t("no_records")}</div>'
                    html_str += "</div>"
                    st.markdown(html_str, unsafe_allow_html=True)

# ── Tab 2: 查詢 ──────────────────────────────────────────────
with tab_lookup:
    st.subheader(t("tab_lookup"))
    st.markdown(f"<span style='color:var(--text-muted);font-size:0.9em;'>{t('div_lookup_desc', default='輸入股票代碼即可查詢其過往所有的除權息紀錄，資料由系統自動從公開數據源獲取。')}</span>", unsafe_allow_html=True)
    
    col_search, col_space = st.columns([1, 2])
    with col_search:
        lookup_sym = st.text_input(t("enter_symbol", default="輸入股票代碼 (例如: FPT, HPG):"), max_chars=10).upper().strip()
    
    if lookup_sym:
        with st.spinner(t("fetching_hist", sym=lookup_sym, n="", default=f"正在查詢 {lookup_sym} 的歷史除權息紀錄...")):
            from market_data import get_dividend_history
            lookup_df = pd.DataFrame(get_dividend_history(lookup_sym))
            
        if lookup_df.empty:
            st.warning(t("div_not_found", sym=lookup_sym))
        else:
            st.markdown(t("div_hist_title", sym=lookup_sym))
            
            # --- 1. 增設頂部統計圖表 (Add Dividend Chart Dashboard) ---
            import plotly.graph_objects as go
            lookup_df["ex_year"] = pd.to_datetime(lookup_df["ex_date"], errors="coerce").dt.year
            yearly_stats = []
            for y in sorted(lookup_df["ex_year"].dropna().unique(), reverse=False):
                y_df = lookup_df[lookup_df["ex_year"] == y]
                c_sum = y_df[y_df["type"] == "CASH"]["cash_amount"].sum()
                s_sum = y_df[y_df["type"] == "STOCK"]["stock_ratio"].sum()
                yearly_stats.append({"Year": str(int(y)), "Cash": c_sum, "Stock": s_sum})
                
            if yearly_stats:
                stats_df = pd.DataFrame(yearly_stats)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=stats_df["Year"], y=stats_df["Cash"],
                    name=t("div_cash_vnd"), marker_color="#10b981", yaxis="y1"
                ))
                fig.add_trace(go.Bar(
                    x=stats_df["Year"], y=stats_df["Stock"],
                    name=t("div_stock_ratio"), marker_color="#60a5fa", yaxis="y2"
                ))
                fig.update_layout(
                    title=t("div_dashboard_title"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8"),
                    xaxis=dict(type="category", showgrid=False),
                    yaxis=dict(title=t("div_cash_vnd"), side="left", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                    yaxis2=dict(title=t("div_stock_ratio"), side="right", overlaying="y", showgrid=False),
                    margin=dict(l=0, r=0, t=40, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # --- 2. 引入類型過濾頁籤 (Type Filters) ---
            try:
                filter_tab = st.pills(t("div_filter_type"), [t("div_type_all"), t("div_type_cash"), t("div_type_stock")], default=t("div_type_all"))
            except:
                filter_tab = st.radio(t("div_filter_type"), [t("div_type_all"), t("div_type_cash"), t("div_type_stock")], horizontal=True, label_visibility="collapsed")
            
            if not filter_tab:
                filter_tab = t("div_type_all")
                
            if filter_tab == t("div_type_cash"):
                filtered_lookup = lookup_df[lookup_df["type"] == "CASH"]
            elif filter_tab == t("div_type_stock"):
                filtered_lookup = lookup_df[lookup_df["type"] == "STOCK"]
            else:
                filtered_lookup = lookup_df
                
            filtered_lookup = filtered_lookup.sort_values("ex_date", ascending=False)
            
            # --- 3. 表格改用年度聚合與折疊 (Group by Year) ---
            html_str = """
<style>
.acc-header { display: grid; align-items: center; }
.acc-row { display: grid; align-items: center; cursor: pointer; }
.acc-sub-row { display: grid; align-items: center; }
.acc-col-left { text-align: left; }
.acc-col-right { text-align: right; }
.acc-details summary { list-style: none; outline: none; }
.acc-details summary::-webkit-details-marker { display: none; }
.acc-details[open] .acc-arrow { transform: rotate(90deg); display: inline-block; transition: 0.2s; }
.acc-arrow { display: inline-block; transition: 0.2s; margin-right: 8px; font-size: 10px; color: #64748b; }
</style>
            """
            html_str += '<div class="acc-table" style="max-height: 500px; overflow-y: auto; box-shadow: none; border: 1px solid var(--border-color);">'
            
            if filtered_lookup.empty:
                html_str += f'<div style="color:var(--text-muted); text-align:center; padding: 24px;">{t("div_no_data")}</div>'
            else:
                html_str += f"""
<div class="acc-header" style="grid-template-columns: 1fr 1fr 1fr 1.2fr 1.2fr; border-bottom: 1px solid #334155; padding: 14px 16px;">
    <div class="acc-col-right">{t("ex_date")}<br><span style="font-size:11px;color:#64748b;">(Ngày GDKHQ)</span></div>
    <div class="acc-col-right">{t("record_date")}<br><span style="font-size:11px;color:#64748b;">(Ngày chốt)</span></div>
    <div class="acc-col-right">{t("pay_date")}<br><span style="font-size:11px;color:#64748b;">(Ngày thực hiện)</span></div>
    <div class="acc-col-left" style="padding-left:16px;">{t("div_type")}<br><span style="font-size:11px;color:#64748b;">(Loại cổ tức)</span></div>
    <div class="acc-col-right">{t("div_amount")}<br><span style="font-size:11px;color:#64748b;">(Tỷ lệ / Giá trị)</span></div>
</div>
                """
                
                years = sorted(filtered_lookup["ex_year"].dropna().unique(), reverse=True)
                for y in years:
                    year = int(y)
                    y_df = filtered_lookup[filtered_lookup["ex_year"] == y].sort_values("ex_date", ascending=False)
                    y_cash = y_df[y_df["type"] == "CASH"]["cash_amount"].sum()
                    y_stock = y_df[y_df["type"] == "STOCK"]["stock_ratio"].sum() * 100
                    
                    html_str += f"""
<details class="acc-details" open>
<summary>
<div class="acc-row" style="grid-template-columns: 1fr 1fr 1.5fr; border-bottom: 1px solid #334155; background: rgba(255,255,255,0.02);">
<div class="acc-col-left">
<span class="tlt-main"><span class="acc-arrow">▶</span>{int(y)} 年度</span>
</div>
<div class="acc-col-right">
<span style="font-size:12px;color:#94a3b8;">累計現金：</span>
<span style="color:#10b981;font-weight:600;font-size:15px;">{c_str}</span>
</div>
<div class="acc-col-right">
<span style="font-size:12px;color:#94a3b8;">累計配股：</span>
<span style="color:#60a5fa;font-weight:600;font-size:15px;">{s_str}</span>
</div>
</div>
</summary>
                    """
                    
                    for _, row in y_df.iterrows():
                        ex_date = row.get("ex_date", "─")
                        rec_date = row.get("record_date", "─")
                        if pd.isna(rec_date) or not rec_date: rec_date = "─"
                        pay_date = row.get("pay_date", "─")
                        if pd.isna(pay_date) or not pay_date: pay_date = "─"
                        
                        if row["type"] == "CASH":
                            dtype = t("div_cash_lbl")
                            amt_main = f"{row['cash_amount']:,.0f} VNĐ"
                            amt_color = "#f8fafc"
                            badge_bg = "#065f46"
                            badge_text = "#34d399"
                        else:
                            dtype = t("div_stock_lbl")
                            amt_main = f"100 : {row['stock_ratio']*100:g}"
                            amt_color = "#f8fafc"
                            badge_bg = "#1e3a8a"
                            badge_text = "#60a5fa"
                            
                        html_str += f"""
<div class="acc-sub-row" style="grid-template-columns: 1fr 1fr 1fr 1.2fr 1.2fr; border-bottom: 1px solid #334155; padding: 14px 16px;">
<div class="acc-col-right" style="color: #00F0FF;">{ex_date}</div>
<div class="acc-col-right" style="color: #00F0FF;">{rec_date}</div>
<div class="acc-col-right" style="color: #00F0FF;">{pay_date}</div>
<div class="acc-col-left" style="padding-left:16px;">
<span style="background: {badge_bg}; padding: 4px 8px; border-radius: 4px; font-size: 12px; color: {badge_text};">{dtype}</span>
</div>
<div class="acc-col-right" style="font-weight: 700; color: {amt_color}; font-size: 16px;">{amt_main}</div>
</div>
                        """
                    html_str += "</details>"
                    
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
