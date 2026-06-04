import streamlit as st
from i18n import t
from supabase_db import sb_save_imap_settings, sb_load_imap_settings

st.title(f"⚙️ {t('nav_settings')}")

user_id = st.session_state.get("user_id")

st.markdown(f"### 📧 {t('imap_sync_title')}")
st.markdown(t("imap_sync_desc"))

# 載入現有設定
settings = sb_load_imap_settings(user_id)
default_email = settings.get("imap_email", "")
default_password = settings.get("imap_password", "")
default_broker = settings.get("broker_name", "TCBS")

with st.form("imap_settings_form"):
    imap_email = st.text_input(t("imap_email"), value=default_email, placeholder="yourname@gmail.com")
    imap_password = st.text_input(t("imap_password"), value=default_password, type="password", placeholder=t("imap_pw_placeholder"))
    
    broker_options = ["TCBS", "SSI", "VNDIRECT", "PHS", t("broker_all")]
    try:
        broker_index = broker_options.index(default_broker)
    except ValueError:
        broker_index = 0
        
    broker_name = st.selectbox(t("broker_select"), options=broker_options, index=broker_index)
    
    st.markdown(t("app_pw_guide"), unsafe_allow_html=True)
    
    submit = st.form_submit_button(t("save_settings"), type="primary")
    if submit:
        if imap_email and imap_password:
            sb_save_imap_settings(user_id, imap_email, imap_password, broker_name)
            st.success(t("settings_saved"))
        else:
            st.error(t("fill_email_pw"))

st.markdown("---")
st.markdown(t("manual_sync_title"))

import datetime

col1, col2 = st.columns([1, 1])
with col1:
    start_date = st.date_input("選擇同步開始日期 (預設為今天)", value=datetime.date.today())
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    sync_clicked = st.button(t("sync_now"), use_container_width=True)

if sync_clicked:
    from email_parser import run_email_sync
    with st.spinner(t("syncing_msg")):
        try:
            # Convert date to datetime for consistency if needed, though email_parser expects a datetime object with strftime
            sync_start = datetime.datetime.combine(start_date, datetime.datetime.min.time())
            results = run_email_sync(user_id, start_date=sync_start)
            st.success(t("sync_success", found=results.get("found", 0), inserted=results.get("inserted", 0)))
            if results.get('inserted', 0) > 0:
                st.balloons()
            elif results.get('found', 0) > 0 and results.get('debug_text'):
                with st.expander("🔍 除錯資訊：查看系統萃取出的 PDF 原始文字 (點擊展開)"):
                    st.markdown("如果解析出的股號、買賣或價格有錯，請將下方這段文字複製貼上給 AI 助理，讓他幫您精準調整解析邏輯！")
                    st.code(results.get('debug_text'))
        except Exception as e:
            st.error(t("sync_failed", error=str(e)))
