import re

with open("i18n.py", "r", encoding="utf-8") as f:
    content = f.read()

new_i18n = """
    "nav_settings":         {"vi": "Cài đặt & Tự động", "zh": "設定與自動化"},
    "imap_sync_title":      {"vi": "Đồng bộ Email Tự động", "zh": "自動信箱同步設定 (IMAP)"},
    "imap_email":           {"vi": "Tài khoản Gmail", "zh": "Gmail 帳號"},
    "imap_password":        {"vi": "Mật khẩu Ứng dụng", "zh": "Google 應用程式密碼"},
    "broker_select":        {"vi": "Công ty Chứng khoán", "zh": "主要券商"},
    "save_settings":        {"vi": "Lưu Cài đặt", "zh": "儲存設定"},
    "sync_now":             {"vi": "Đồng bộ Ngay", "zh": "立即手動同步"},
"""

target = """def get_lang() -> str:"""

if target in content:
    content = content.replace(target, new_i18n + "\n\n" + target)
    with open("i18n.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Added settings i18n")
