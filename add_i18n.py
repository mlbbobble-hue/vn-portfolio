import re

with open("i18n.py", "r", encoding="utf-8") as f:
    content = f.read()

new_translations = """
    # --- New Chart Strings ---
    "display_twd":          {"vi": "Hiển thị bằng TWD 🇹🇼", "zh": "顯示為台幣 (TWD) 🇹🇼"},
    "current_principal":    {"vi": "Vốn gốc hiện tại", "zh": "當前投入本金"},
    "realized_pl_chart":    {"vi": "Lãi/Lỗ đã chốt", "zh": "已實現損益"},
    "unrealized_pl_chart":  {"vi": "Lãi/Lỗ chưa chốt", "zh": "未實現損益"},
    "cash_div_chart":       {"vi": "Cổ tức tiền mặt", "zh": "現金配息"},
    "stock_div_chart":      {"vi": "GT Cổ tức cổ phiếu", "zh": "配股現值"},
    "total_net_profit":     {"vi": "Tổng Lợi nhuận ròng", "zh": "總投資淨利"},
    "pl_waterfall":         {"vi": "Biểu đồ Thác nước L/L", "zh": "損益瀑布圖 (P&L Waterfall)"},
    "portfolio_heatmap":    {"vi": "Bản đồ nhiệt Danh mục", "zh": "投資組合熱力圖"},
    "pie_chart":            {"vi": "Biểu đồ tròn", "zh": "持股圓餅圖"},
    "broker_dist":          {"vi": "Phân bổ theo CTCK", "zh": "券股市值分佈"},
    "asset_dist":           {"vi": "Phân bổ Tài sản", "zh": "持股資產配置"},
    "broker_only":          {"vi": "CTCK", "zh": "券商"},
    "current_price":        {"vi": "Giá HT", "zh": "目前市價"},
    "unrealized_vnd":       {"vi": "Lãi/Lỗ chưa chốt (VND)", "zh": "未實現損益 (VND)"},
    "total_inventory":      {"vi": "Tổng Cổ phiếu", "zh": "總庫存 (股)"},
    "fund_accum_history":   {"vi": "Lịch sử tích lũy vốn", "zh": "資金累積與歷史操作"},
    "chart_date":           {"vi": "Ngày", "zh": "日期"},
    "chart_type":           {"vi": "Loại", "zh": "類型"},
    "chart_shares":         {"vi": "Cổ phiếu", "zh": "股數"},
    "chart_price":          {"vi": "Giá", "zh": "價格"},
    "chart_fee":            {"vi": "Phí", "zh": "手續費"},
    "chart_tax":            {"vi": "Thuế", "zh": "稅金"},
    "cash_div_ytd":         {"vi": "Cổ tức Tiền mặt YTD", "zh": "今年累計領取配息 (Cash Div)"},
    "cash_div_pending":     {"vi": "Cổ tức TM chờ nhận", "zh": "即將入帳配息 (Pending Cash)"},
    "cash_div_all_time":    {"vi": "Cổ tức TM Lịch sử", "zh": "歷史累計配息 (All-time Cash)"},
    "stock_div_ytd":        {"vi": "Cổ tức Cổ phiếu YTD", "zh": "今年領取配股現值 (Stock Div Value)"},
    "stock_div_pending":    {"vi": "Cổ tức CP chờ nhận", "zh": "即將發放配股現值 (Pending Stock)"},
    "stock_div_all_time":   {"vi": "Cổ tức CP Lịch sử", "zh": "歷史累計配股現值 (All-time Stock)"},
"""

if '"display_twd"' not in content:
    content = content.replace('\n}\n\n\ndef get_lang()', new_translations + '\n}\n\n\ndef get_lang()')
    with open("i18n.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("i18n updated correctly!")
else:
    print("Already there.")
