import re

# 00_dashboard.py
with open("views/00_dashboard.py", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('st.toggle("顯示為台幣 (TWD) 🇹🇼", value=False)', 'st.toggle(t("display_twd"), value=False)')
c = c.replace('wf_x = ["已實現損益", "未實現損益", "現金配息", "配股現值", "總投資淨利"]', 'wf_x = [t("realized_pl_chart"), t("unrealized_pl_chart"), t("cash_div_chart"), t("stock_div_chart"), t("total_net_profit")]')
c = c.replace('wf_title = "損益瀑布圖 (P&L Waterfall)" if lang == "zh" else "Biểu đồ Thác nước Lãi/Lỗ"', 'wf_title = t("pl_waterfall")')
c = c.replace('st.markdown("<h4 style=\'margin-left: 8px;\'>投資組合熱力圖</h4>", unsafe_allow_html=True)', 'st.markdown(f"<h4 style=\'margin-left: 8px;\'>{t(\'portfolio_heatmap\')}</h4>", unsafe_allow_html=True)')

with open("views/00_dashboard.py", "w", encoding="utf-8") as f:
    f.write(c)

# 01_portfolio.py
with open("views/01_portfolio.py", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('text="<b>券股市值分佈</b>"', 'text=f"<b>{t(\'broker_dist\')}</b>"')
c = c.replace('text="<b>持股資產配置</b>"', 'text=f"<b>{t(\'asset_dist\')}</b>"')

with open("views/01_portfolio.py", "w", encoding="utf-8") as f:
    f.write(c)

# 02_transactions.py
with open("views/02_transactions.py", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('text="<b>資金累積與歷史操作</b>"', 'text=f"<b>{t(\'fund_accum_history\')}</b>"')

with open("views/02_transactions.py", "w", encoding="utf-8") as f:
    f.write(c)

# 03_dividends.py
with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('今年累計領取配息 (Cash Div)', '{t("cash_div_ytd")}')
c = c.replace('即將入帳配息 (Pending Cash)', '{t("cash_div_pending")}')
c = c.replace('歷史累計配息 (All-time Cash)', '{t("cash_div_all_time")}')
c = c.replace('今年領取配股現值 (Stock Div Value)', '{t("stock_div_ytd")}')
c = c.replace('即將發放配股現值 (Pending Stock)', '{t("stock_div_pending")}')
c = c.replace('歷史累計配股現值 (All-time Stock)', '{t("stock_div_all_time")}')

c = c.replace('df_monthly["type_str"] = df_monthly["type"].map({"CASH": "現金配息", "STOCK": "配股現值"})', 'df_monthly["type_str"] = df_monthly["type"].map({"CASH": t("cash_div_chart"), "STOCK": t("stock_div_chart")})')

c = c.replace('color_discrete_map={"現金配息": "#00F0FF", "配股現值": "#FF007F"}', 'color_discrete_map={t("cash_div_chart"): "#00F0FF", t("stock_div_chart"): "#FF007F"}')
c = c.replace('bar_title = "每月被動收入趨勢" if lang == "zh" else "Xu hướng thu nhập thụ động hàng tháng"', 'bar_title = "每月被動收入趨勢" if st.session_state.get("lang", "zh") == "zh" else "Xu hướng thu nhập thụ động hàng tháng"')

with open("views/03_dividends.py", "w", encoding="utf-8") as f:
    f.write(c)

print("Translations replaced")
