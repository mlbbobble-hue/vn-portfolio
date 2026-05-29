"""頁面2：交易記錄（雙語 + db_router）"""
import streamlit as st
import pandas as pd
from datetime import date
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (add_transaction, delete_transaction,
                        get_all_transactions, import_transactions_from_csv)
from config import BROKERS

st.set_page_config(page_title=f"VN Portfolio | {t('transactions_title')}", page_icon="📝", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);color:#e2e8f0;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1e1e3a 0%,#16213e 100%);border-right:1px solid rgba(99,102,241,0.2);}
.card{background:linear-gradient(135deg,rgba(30,30,60,0.8),rgba(20,20,45,0.9));border:1px solid rgba(99,102,241,0.3);border-radius:16px;padding:20px 24px;margin:8px 0;}
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
    <h2 style='margin:0;color:#e2e8f0;'>{t('transactions_title')}</h2>
    <p style='margin:4px 0 0;color:#94a3b8;font-size:0.9rem;'>{t('transactions_desc')}</p>
</div>""", unsafe_allow_html=True)

tab_add, tab_import, tab_view = st.tabs([t("add_transaction"), t("tab_import"), t("tab_view")])

# ── Tab 1: 新增 ─────────────────────────────────────────────
with tab_add:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(t("add_tx_title"))
    c1, c2, c3 = st.columns(3)
    with c1:
        txn_date   = st.date_input(t("tx_date"), value=date.today(), key="add_date")
        txn_broker = st.selectbox(t("tx_broker"), BROKERS, key="add_broker")
    with c2:
        txn_symbol = st.text_input(t("tx_symbol"), placeholder="FPT", key="add_sym").upper()
        txn_action = st.radio(t("tx_action"), [t("buy_action"), t("sell_action")],
                              horizontal=True, key="add_action")
    with c3:
        txn_shares = st.number_input(t("tx_shares"), min_value=1, step=100, value=100, key="add_shares")
        txn_price  = st.number_input(t("tx_price"), min_value=100, step=100, value=100000, key="add_price")

    txn_fee  = st.number_input(t("tx_fee"), min_value=0, value=int(txn_shares*txn_price*0.0015), key="add_fee")
    txn_note = st.text_input(t("tx_note"), key="add_note")

    action_code = "BUY" if "BUY" in txn_action or "Mua" in txn_action or "買" in txn_action else "SELL"
    total_val = txn_shares * txn_price
    net_val   = total_val + txn_fee if action_code == "BUY" else total_val - txn_fee
    st.markdown(f"""
    <div style='background:rgba(99,102,241,0.1);border-radius:10px;padding:12px 16px;margin:12px 0;border:1px solid rgba(99,102,241,0.3);'>
        <span style='color:#94a3b8;font-size:.85rem;'>{t('tx_preview')}　</span>
        <b style='color:#a78bfa;font-size:1.1rem;'>{total_val:,.0f} {t('vnd')}</b>
        <span style='color:#64748b;'> + {txn_fee:,.0f} = </span>
        <b style='color:#34d399;'>{net_val:,.0f} {t('vnd')}</b>
    </div>""", unsafe_allow_html=True)

    if st.button(t("tx_add_confirm"), use_container_width=True):
        if not txn_symbol:
            st.error(t("enter_symbol"))
        else:
            add_transaction(str(txn_date), txn_broker, txn_symbol, action_code,
                            txn_shares, txn_price, txn_fee, txn_note)
            st.success(f"✅ {action_code} {txn_symbol} × {txn_shares:,} @ {txn_price:,}")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 2: 匯入 ─────────────────────────────────────────────
with tab_import:
    st.subheader(t("tab_import"))
    st.markdown(t("csv_format_hint"))
    st.markdown("""
    | date | broker | symbol | action | shares | price | fee | note |
    |------|--------|--------|--------|--------|-------|-----|------|
    | 2024-01-15 | TCBS | FPT | BUY | 1000 | 115000 | 172 | ... |
    """)
    sample = pd.DataFrame({
        "date":["2024-01-15","2024-03-10"],"broker":["TCBS","PHS"],
        "symbol":["FPT","TCB"],"action":["BUY","BUY"],
        "shares":[1000,2000],"price":[115000,25000],"fee":[172,75],"note":["",""],
    })
    st.download_button(t("download_template"), data=sample.to_csv(index=False).encode("utf-8-sig"),
                       file_name="template.csv", mime="text/csv")
    uploaded = st.file_uploader(t("upload_csv"), type=["csv"])
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            st.dataframe(df_up.head(10), use_container_width=True)
            if st.button(t("confirm_import"), use_container_width=True):
                cnt = import_transactions_from_csv(df_up)
                st.success(t("import_ok", n=cnt))
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
                  .applymap(hl, subset=[t("col_action")]))
        st.dataframe(styled, use_container_width=True, height=360)

        st.markdown("---")
        st.subheader(t("delete_tx_title"))
        del_id = st.number_input(t("delete_tx_hint"), min_value=1, step=1, key="del_id")
        if st.button(t("delete_tx_btn"), use_container_width=True):
            if del_id in all_txns["id"].values:
                delete_transaction(int(del_id))
                st.success(t("delete_ok", id=del_id))
                st.rerun()
            else:
                st.error(t("not_found", id=del_id))
