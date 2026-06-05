import re

with open("i18n.py", "r", encoding="utf-8") as f:
    content = f.read()

new_i18n = """
    "imap_sync_desc":       {"vi": "Cài đặt Mật khẩu Ứng dụng Gmail của bạn. Hệ thống sẽ tự động đọc email báo cáo giao dịch từ công ty chứng khoán và cập nhật danh mục đầu tư.", "zh": "設定您的 Gmail 應用程式密碼，系統將能自動讀取您的券商成交回報信件，並更新您的投資組合。"},
    "imap_pw_placeholder":  {"vi": "16 ký tự chữ cái (không có khoảng trắng)", "zh": "16位英文字母 (無空白)"},
    "broker_all":           {"vi": "ALL (Tìm kiếm tất cả)", "zh": "ALL (搜尋全部券商)"},
    "app_pw_guide":         {"vi": "> **Cách lấy Mật khẩu Ứng dụng Google?**<br>> 1. Truy cập Cài đặt Tài khoản Google > Bảo mật.<br>> 2. Đảm bảo 'Xác minh 2 bước' đã bật.<br>> 3. Tìm kiếm và nhấp vào 'Mật khẩu ứng dụng'.<br>> 4. Tạo một mật khẩu 16 chữ cái mới và dán vào bên trên.", "zh": "> **如何取得 Google 應用程式密碼？**<br>> 1. 前往您的 Google 帳戶設定 > 安全性。<br>> 2. 確保已開啟「兩步驟驗證」。<br>> 3. 搜尋並點擊「應用程式密碼」。<br>> 4. 產生一組新的 16 位密碼並貼到上方。"},
    "settings_saved":       {"vi": "Đã lưu cài đặt!", "zh": "設定已儲存！"},
    "fill_email_pw":        {"vi": "Vui lòng điền đầy đủ Email và Mật khẩu!", "zh": "請填寫完整的 Email 與密碼！"},
    "manual_sync_title":    {"vi": "### 🔄 Kiểm tra đồng bộ thủ công", "zh": "### 🔄 手動測試同步"},
    "syncing_msg":          {"vi": "Đang kết nối tới Gmail và đọc thư...", "zh": "正在連線至 Gmail 並讀取信件..."},
    "sync_success":         {"vi": "Đồng bộ hoàn tất! Tìm thấy {found} email, nhập thành công {inserted} giao dịch.", "zh": "同步完成！共找到 {found} 封信件，成功匯入 {inserted} 筆交易紀錄。"},
    "sync_failed":          {"vi": "Đồng bộ thất bại: {error}", "zh": "同步失敗: {error}"},
"""

target = """    "sync_now":             {"vi": "Đồng bộ Ngay", "zh": "立即手動同步"},
}"""

if target in content:
    content = content.replace(target, '    "sync_now":             {"vi": "Đồng bộ Ngay", "zh": "立即手動同步"},\n' + new_i18n + "}")
    with open("i18n.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Added new translations to i18n.py")
else:
    print("Target not found in i18n.py")
