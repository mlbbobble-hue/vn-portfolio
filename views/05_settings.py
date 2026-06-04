import streamlit as st
from i18n import t
from supabase_db import sb_save_imap_settings, sb_load_imap_settings

st.title(f"⚙️ {t('nav_settings')}")

user_id = st.session_state.get("user_id")

st.markdown(f"### 📧 {t('imap_sync_title')}")
st.markdown("設定您的 Gmail 應用程式密碼，系統將能自動讀取您的券商成交回報信件，並更新您的投資組合。")

# 載入現有設定
settings = sb_load_imap_settings(user_id)
default_email = settings.get("imap_email", "")
default_password = settings.get("imap_password", "")
default_broker = settings.get("broker_name", "TCBS")

with st.form("imap_settings_form"):
    imap_email = st.text_input(t("imap_email"), value=default_email, placeholder="yourname@gmail.com")
    imap_password = st.text_input(t("imap_password"), value=default_password, type="password", placeholder="16位英文字母 (無空白)")
    
    broker_options = ["TCBS", "SSI", "VNDIRECT", "Other"]
    try:
        broker_index = broker_options.index(default_broker)
    except ValueError:
        broker_index = 0
        
    broker_name = st.selectbox(t("broker_select"), options=broker_options, index=broker_index)
    
    st.markdown("""
    > **如何取得 Google 應用程式密碼？**
    > 1. 前往您的 Google 帳戶設定 > 安全性。
    > 2. 確保已開啟「兩步驟驗證」。
    > 3. 搜尋並點擊「應用程式密碼」。
    > 4. 產生一組新的 16 位密碼並貼到上方。
    """)
    
    submit = st.form_submit_button(t("save_settings"), type="primary")
    if submit:
        if imap_email and imap_password:
            sb_save_imap_settings(user_id, imap_email, imap_password, broker_name)
            st.success("設定已儲存！")
        else:
            st.error("請填寫完整的 Email 與密碼！")

st.markdown("---")
st.markdown("### 🔄 手動測試同步")

if st.button(t("sync_now"), use_container_width=True):
    from email_parser import run_email_sync
    with st.spinner("正在連線至 Gmail 並讀取信件..."):
        try:
            results = run_email_sync(user_id)
            st.success(f"同步完成！共找到 {results.get('found', 0)} 封信件，成功匯入 {results.get('inserted', 0)} 筆交易紀錄。")
            if results.get('inserted', 0) > 0:
                st.balloons()
        except Exception as e:
            st.error(f"同步失敗: {e}")
