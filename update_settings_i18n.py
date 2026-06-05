import re

with open("views/05_settings.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('st.markdown("設定您的 Gmail 應用程式密碼，系統將能自動讀取您的券商成交回報信件，並更新您的投資組合。")', 'st.markdown(t("imap_sync_desc"))')
content = content.replace('placeholder="16位英文字母 (無空白)"', 'placeholder=t("imap_pw_placeholder")')
content = content.replace('"ALL (搜尋全部券商)"', 't("broker_all")')
content = content.replace('st.success("設定已儲存！")', 'st.success(t("settings_saved"))')
content = content.replace('st.error("請填寫完整的 Email 與密碼！")', 'st.error(t("fill_email_pw"))')
content = content.replace('st.markdown("### 🔄 手動測試同步")', 'st.markdown(t("manual_sync_title"))')
content = content.replace('with st.spinner("正在連線至 Gmail 並讀取信件..."):', 'with st.spinner(t("syncing_msg")):')
content = content.replace('st.success(f"同步完成！共找到 {results.get(\'found\', 0)} 封信件，成功匯入 {results.get(\'inserted\', 0)} 筆交易紀錄。")', 'st.success(t("sync_success", found=results.get("found", 0), inserted=results.get("inserted", 0)))')
content = content.replace('st.error(f"同步失敗: {e}")', 'st.error(t("sync_failed", error=str(e)))')

target_guide = '''    st.markdown("""
    > **如何取得 Google 應用程式密碼？**
    > 1. 前往您的 Google 帳戶設定 > 安全性。
    > 2. 確保已開啟「兩步驟驗證」。
    > 3. 搜尋並點擊「應用程式密碼」。
    > 4. 產生一組新的 16 位密碼並貼到上方。
    """)'''

if target_guide in content:
    content = content.replace(target_guide, '    st.markdown(t("app_pw_guide"), unsafe_allow_html=True)')
else:
    print("Warning: Target guide not found.")

with open("views/05_settings.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated 05_settings.py for full i18n")
