"""頁面2：交易記錄（雙語 + db_router）"""
import streamlit as st
import pandas as pd
from datetime import date
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (add_transaction, delete_transaction,
                        get_all_transactions, import_transactions_from_csv,
                        update_transaction)
from config import BROKERS

st.set_page_config(page_title=f"VN Portfolio | {t('transactions_title')}", page_icon="📝", layout="wide")
from theme import load_css
load_css()

if not check_auth():
    st.stop()

st.markdown(f"""
<div class="page-header">
    <h2>{t('transactions_title')}</h2>
    <p>{t('transactions_desc')}</p>
</div>""", unsafe_allow_html=True)

tab_add, tab_import, tab_view = st.tabs([t("add_transaction"), t("tab_import"), t("tab_view")])

# ── Tab 1: 新增 ─────────────────────────────────────────────
with tab_add:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(t("add_tx_title"))
    
    # 資產類型選擇
    asset_type = st.radio(
        "📦 資產類型",
        ["📈 股票 (Stock)", "🏦 債券 (Bond)"],
        horizontal=True, key="asset_type"
    )
    is_bond = "Bond" in asset_type or "債券" in asset_type
    
    c1, c2, c3 = st.columns(3)
    with c1:
        txn_date   = st.date_input(t("tx_date"), value=date.today(), key="add_date")
        txn_broker = st.selectbox(t("tx_broker"), BROKERS, key="add_broker")
    with c2:
        if is_bond:
            txn_symbol = st.text_input("🏦 債券代號 / 名稱", placeholder="CII424002", key="add_sym").upper()
        else:
            txn_symbol = st.text_input(t("tx_symbol"), placeholder="FPT", key="add_sym").upper()
        txn_action = st.radio(t("tx_action"), [t("buy_action"), t("sell_action")],
                              horizontal=True, key="add_action")
    with c3:
        txn_shares = st.number_input(t("tx_shares"), min_value=1, step=100, value=100, key="add_shares")
        txn_price  = st.number_input(
            "💰 買入/賣出價格 (VND)" if is_bond else t("tx_price"),
            min_value=100, step=100, value=100000, key="add_price"
        )
    
    # 債券專屬：手動輸入目前市場價格
    if is_bond:
        st.markdown("---")
        st.markdown("##### 🏦 債券額外資訊")
        bond_market_price = st.number_input(
            "📊 目前市場價格 (VND)",
            min_value=0, step=1000, value=txn_price,
            help=t("bond_price_help"),
            key="bond_market_price"
        )
    
    txn_fee  = st.number_input(t("tx_fee"), min_value=0, value=int(txn_shares*txn_price*0.0015), key="add_fee")
    txn_note = st.text_input(t("tx_note"), key="add_note")

    action_code = "BUY" if "BUY" in txn_action or "Mua" in txn_action or "買" in txn_action else "SELL"
    total_val = txn_shares * txn_price
    net_val   = total_val + txn_fee if action_code == "BUY" else total_val - txn_fee
    
    if is_bond:
        st.markdown(f"""
        <div style='background:rgba(59,130,246,0.1);border-radius:10px;padding:12px 16px;margin:12px 0;border:1px solid rgba(59,130,246,0.3);'>
            <span style='color:#64748b;font-size:.85rem;'>🏦 債券交易預覽　</span>
            <b style='color:#1e293b;font-size:1.1rem;'>{total_val:,.0f} {t('vnd')}</b>
            <span style='color:#64748b;'> + 手續費 {txn_fee:,.0f} = </span>
            <b style='color:#3b82f6;'>{net_val:,.0f} {t('vnd')}</b>
            <br><span style='color:#64748b;font-size:.8rem;'>📊 目前市場價格: {bond_market_price:,.0f} VND | ⚠️ 此債券不參與自動股價更新</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background:rgba(99,102,241,0.1);border-radius:10px;padding:12px 16px;margin:12px 0;border:1px solid rgba(99,102,241,0.3);'>
            <span style='color:var(--text-muted);font-size:.85rem;'>{t('tx_preview')}　</span>
            <b style='color:var(--text-primary);font-size:1.1rem;'>{total_val:,.0f} {t('vnd')}</b>
            <span style='color:#64748b;'> + {txn_fee:,.0f} = </span>
            <b style='color:#34d399;'>{net_val:,.0f} {t('vnd')}</b>
        </div>""", unsafe_allow_html=True)

    if st.button(t("tx_add_confirm"), use_container_width=True):
        if not txn_symbol:
            st.error(t("enter_symbol"))
        else:
            # 如果是債券，在 note 前面加上 [BOND] 標記
            final_note = f"[BOND] {txn_note}".strip() if is_bond else txn_note
            add_transaction(str(txn_date), txn_broker, txn_symbol, action_code,
                            txn_shares, txn_price, txn_fee, final_note)
            
            # 如果是債券，手動寫入市場價格到 price_cache
            if is_bond:
                from db_router import upsert_price_cache
                upsert_price_cache(txn_symbol, bond_market_price, 0, 0)
            
            emoji = "🏦" if is_bond else "✅"
            asset_label = "債券" if is_bond else ""
            st.success(f"{emoji} {action_code} {asset_label} {txn_symbol} × {txn_shares:,} @ {txn_price:,}")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── Tab 2: 匯入 ─────────────────────────────────────────────
with tab_import:
    st.subheader(t("tab_import"))
    
    import_mode = st.radio(t("import_mode"), [t("import_snapshot"), t("import_history")], horizontal=True)
    
    if import_mode == t("import_history"):
        st.markdown(t("csv_format_hint") + "：系統會自動嘗試尋找對應的欄位，您也可以手動指定。")
        sample = pd.DataFrame({
            "date":["2024-01-15","2024-03-10"],"broker":["TCBS","PHS"],
            "symbol":["FPT","TCB"],"action":["BUY","BUY"],
            "shares":[1000,2000],"price":[115000,25000],"fee":[172,75],"note":["",""],
        })
    else:
        st.markdown("💡 **持股快照模式**：只要提供「股票代號」、「股數」與「總成本(或平均價格)」，系統會自動將它們轉換為今天的買進紀錄！")
        sample = pd.DataFrame({
            "symbol":["FPT","TCB"],
            "shares":[1000,2000],
            "total_cost":[115000000,50000000]
        })
        
    st.download_button(t("download_template"), data=sample.to_csv(index=False).encode("utf-8-sig"),
                       file_name="template.csv", mime="text/csv")
                       
    uploaded = st.file_uploader(t("upload_csv"), type=["csv"])
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            cols = list(df_up.columns)
            st.write(t("preview_raw_data"))
            st.dataframe(df_up.head(3), use_container_width=True)
            
            st.markdown("### 🔗 欄位對應 (Column Mapping)")
            
            def guess_col(keywords, options):
                for opt in options:
                    for kw in keywords:
                        if kw.lower() in str(opt).lower(): return opt
                return options[0] if options else None

            if import_mode == t("import_history"):
                col1, col2, col3, col4 = st.columns(4)
                with col1: map_date = st.selectbox(t("col_date"), cols, index=cols.index(guess_col(["date", "日期", "時間"], cols)))
                with col2: map_sym = st.selectbox(t("col_symbol"), cols, index=cols.index(guess_col(["symbol", "ticker", "代號", "股票"], cols)))
                with col3: map_act = st.selectbox(t("col_action"), cols, index=cols.index(guess_col(["action", "動作", "買賣", "type"], cols)))
                with col4: map_shares = st.selectbox(t("col_shares"), cols, index=cols.index(guess_col(["share", "qty", "股數", "數量"], cols)))
                
                col5, col6, col7, col8 = st.columns(4)
                with col5: map_price = st.selectbox(t("col_price"), cols, index=cols.index(guess_col(["price", "價格", "單價"], cols)))
                with col6: map_broker = st.selectbox(t("col_broker"), [t("manual_input")] + cols, index=0)
                if map_broker == t("manual_input"): manual_broker = st.selectbox(t("default_broker"), BROKERS)
                with col7: map_fee = st.selectbox(t("col_fee"), [t("no_fee_note")] + cols, index=0)
                with col8: map_note = st.selectbox(t("col_note"), [t("no_fee_note")] + cols, index=0)
                
                if st.button("プレビュー (預覽轉換後資料)"):
                    mapped_df = pd.DataFrame()
                    mapped_df["date"] = df_up[map_date]
                    mapped_df["symbol"] = df_up[map_sym]
                    mapped_df["action"] = df_up[map_act]
                    mapped_df["shares"] = pd.to_numeric(df_up[map_shares].astype(str).str.replace(",",""), errors="coerce")
                    mapped_df["price"] = pd.to_numeric(df_up[map_price].astype(str).str.replace(",",""), errors="coerce")
                    mapped_df["broker"] = manual_broker if map_broker == t("manual_input") else df_up[map_broker]
                    mapped_df["fee"] = df_up[map_fee] if map_fee != t("no_fee_note") else 0
                    mapped_df["note"] = df_up[map_note] if map_note != t("no_fee_note") else ""
                    st.session_state["mapped_df"] = mapped_df
                    
            else:
                col1, col2, col3 = st.columns(3)
                with col1: map_sym = st.selectbox(t("col_symbol"), cols, index=cols.index(guess_col(["symbol", "ticker", "代號", "股票"], cols)))
                with col2: map_shares = st.selectbox(t("col_shares"), cols, index=cols.index(guess_col(["share", "qty", "股數", "數量"], cols)))
                with col3: 
                    cost_type = st.radio(t("cost_type"), [t("total_cost"), t("avg_price")], horizontal=True)
                    map_cost = st.selectbox(cost_type, cols, index=cols.index(guess_col(["cost", "成本", "price", "價格", "市值", "金額"], cols)))
                
                col_b, col_d = st.columns(2)
                with col_b: snapshot_broker = st.selectbox(t("default_broker_2"), BROKERS)
                with col_d: snapshot_date = st.date_input(t("import_date"), value=date.today())
                
                if st.button(t("preview_parsed_data"), use_container_width=True):
                    mapped_df = pd.DataFrame()
                    mapped_df["symbol"] = df_up[map_sym]
                    mapped_df["date"] = snapshot_date
                    mapped_df["action"] = "BUY"
                    mapped_df["shares"] = pd.to_numeric(df_up[map_shares].astype(str).str.replace(",",""), errors="coerce")
                    mapped_df["broker"] = snapshot_broker
                    mapped_df["fee"] = 0
                    mapped_df["note"] = "Snapshot Import"
                    
                    if "總成本" in cost_type:
                        mapped_df["price"] = pd.to_numeric(df_up[map_cost].astype(str).str.replace(",",""), errors='coerce') / pd.to_numeric(df_up[map_shares].astype(str).str.replace(",",""), errors='coerce')
                    else:
                        mapped_df["price"] = pd.to_numeric(df_up[map_cost].astype(str).str.replace(",",""), errors='coerce')
                        
                    st.session_state["mapped_df"] = mapped_df
            
            if "mapped_df" in st.session_state:
                st.markdown("### ✨ 轉換結果預覽與編輯")
                st.info("💡 您可以直接在下方的表格中點擊欄位進行修改！例如把 HPG_WFT 刪除後綴改回 HPG。改完後再按下確認匯入即可。")
                final_df = st.session_state["mapped_df"].dropna(subset=["symbol", "shares", "price"]).copy()
                
                # Automatically strip _WFT to save user time
                final_df["symbol"] = final_df["symbol"].astype(str).str.replace(r"_WFT$", "", regex=True, flags=re.IGNORECASE)
                
                edited_df = st.data_editor(final_df, use_container_width=True, num_rows="dynamic")
                
                if st.button("✅ 確認匯入", use_container_width=True, type="primary"):
                    cnt = import_transactions_from_csv(edited_df)
                    st.success(t("import_ok", n=cnt))
                    del st.session_state["mapped_df"]
                    st.rerun()
                    
        except Exception as e:
            st.error(t("import_fail", err=e))

# ── Tab 3: 查看 ─────────────────────────────────────────────

with tab_view:
    st.subheader(t("history_title"))
    all_txns = get_all_transactions()
    if all_txns.empty:
        st.info(t("no_data"))
    else:
        fc1, fc2, fc3 = st.columns(3)
        with fc1: fsym = st.text_input(t("filter_symbol"), "").upper()
        with fc2: fbk  = st.selectbox(t("filter_broker"), [t("all")] + list(all_txns["broker"].unique()))
        with fc3: fact = st.selectbox(t("filter_action"), [t("all"), "BUY", "SELL"])

        f = all_txns.copy()
        if fsym: f = f[f["symbol"].str.contains(fsym)]
        if fbk != t("all"):  f = f[f["broker"] == fbk]
        if fact != t("all"): f = f[f["action"] == fact]

        st.markdown(f"<small style='color:#64748b;'>{t('total_records')} {len(f)} {t('records')}</small>", unsafe_allow_html=True)
        f = f.copy()
        f["淨金額"] = f.apply(lambda r: r["shares"]*r["price"] + (r["fee"] if r["action"]=="BUY" else -r["fee"]), axis=1)
        show = f[["id","date","broker","symbol","action","shares","price","fee","淨金額","note"]].rename(columns={
            "id":t("col_id"),"date":t("date"),"broker":t("broker"),"symbol":t("symbol"),
            "action":t("col_action"),"shares":t("shares"),"price":t("price"),
            "fee":t("fee"),"淨金額":t("net_amount"),"note":t("note"),
        })
        def hl(val):
            if val == "BUY":  return "color:#34d399;font-weight:600"
            if val == "SELL": return "color:#f87171;font-weight:600"
            return ""
        styled = (show.style.format({t("shares"):"{:,.0f}",t("price"):"{:,.0f}",
                                     t("fee"):"{:,.0f}",t("net_amount"):"{:,.0f}"})
                  .map(hl, subset=[t("col_action")]))
        st.dataframe(styled, use_container_width=True, height=360)

        st.markdown("---")
        
        # 建立兩個分頁來處理修改和刪除，避免畫面太長
        edit_tab, delete_tab = st.tabs(["✏️ 修改紀錄 (Edit)", "🗑️ 刪除紀錄 (Delete)"])
        
        with edit_tab:
            st.markdown("### ✏️ 修改交易記錄")
            edit_id = st.number_input(t("edit_tx_id"), min_value=1, step=1, key="edit_id")
            
            # 尋找這筆紀錄
            target_record = all_txns[all_txns["id"] == edit_id]
            
            if not target_record.empty:
                r = target_record.iloc[0]
                st.info(t("editing_tx", id=edit_id, act=r["action"], sym=r["symbol"]))
                
                with st.form(key="edit_tx_form"):
                    e1, e2, e3 = st.columns(3)
                    with e1:
                        # 轉換為 date 物件
                        try:
                            d_val = pd.to_datetime(r["date"]).date()
                        except:
                            d_val = date.today()
                        new_date = st.date_input(t("tx_date"), value=d_val, key="e_date")
                        
                        try:
                            broker_idx = BROKERS.index(r["broker"])
                        except ValueError:
                            broker_idx = 0
                        new_broker = st.selectbox(t("tx_broker"), BROKERS, index=broker_idx, key="e_broker")
                    
                    with e2:
                        new_symbol = st.text_input(t("tx_symbol"), value=r["symbol"], key="e_sym").upper()
                        act_idx = 0 if r["action"] == "BUY" else 1
                        new_action = st.radio(t("tx_action"), ["BUY", "SELL"], index=act_idx, horizontal=True, key="e_act")
                    
                    with e3:
                        new_shares = st.number_input(t("tx_shares"), min_value=1.0, value=float(r["shares"]), step=100.0, key="e_shares")
                        new_price = st.number_input(t("tx_price"), min_value=0.0, value=float(r["price"]), step=100.0, key="e_price")
                        
                    new_fee = st.number_input(t("tx_fee"), min_value=0.0, value=float(r.get("fee", 0)), step=1000.0, key="e_fee")
                    new_note = st.text_input(t("tx_note"), value=r.get("note", ""), key="e_note")
                    
                    if st.form_submit_button("✅ 儲存修改 (Save)", use_container_width=True):
                        if not new_symbol:
                            st.error(t("enter_symbol"))
                        else:
                            updates = {
                                "date": str(new_date),
                                "broker": new_broker,
                                "symbol": new_symbol,
                                "action": new_action,
                                "shares": new_shares,
                                "price": new_price,
                                "fee": new_fee,
                                "note": new_note
                            }
                            update_transaction(int(edit_id), updates)
                            st.success(f"✅ 紀錄 ID {edit_id} 修改成功！")
                            st.rerun()
            else:
                if edit_id:
                    st.warning(t("tx_not_found"))
                    
        with delete_tab:
            st.markdown("### 🗑️ 刪除交易記錄")
            del_id = st.number_input(t("delete_tx_hint"), min_value=1, step=1, key="del_id")
            
            # 尋找這筆紀錄預覽
            del_record = all_txns[all_txns["id"] == del_id]
            if not del_record.empty:
                r = del_record.iloc[0]
                st.warning(f"⚠️ 即將刪除: {r['date']} | {r['action']} {r['symbol']} | {r['shares']:,.0f} 股")
            
            if st.button(t("delete_tx_btn"), use_container_width=True, type="primary"):
                if del_id in all_txns["id"].values:
                    delete_transaction(int(del_id))
                    st.success(t("delete_ok", id=del_id))
                    st.rerun()
                else:
                    st.error(t("not_found", id=del_id))
