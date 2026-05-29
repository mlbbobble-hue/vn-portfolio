import os

replacements_dashboard = {
    '"獲利翻倍 (>50%)"': 't("roi_double")',
    '"穩定獲利 (>0%)"': 't("roi_profit")',
    '"微幅虧損 (<0%)"': 't("roi_loss")',
    '"平盤或特殊 (0%)"': 't("roi_flat")',
    '"投資組合"': 't("portfolio")',
    '"前往新增交易"': 't("go_to_add_tx")',
}

replacements_transactions = {
    '"輸入此債券的目前市場報價，系統會用此價格計算市值與損益。此項目不會透過自動更新股價去抓取。"': 't("bond_price_help")',
    '"匯入模式"': 't("import_mode")',
    '"目前持股快照 (Portfolio Snapshot)"': 't("import_snapshot")',
    '"歷史交易明細 (Transaction History)"': 't("import_history")',
    '"預覽原始資料："': 't("preview_raw_data")',
    '"日期 (Date)"': 't("col_date")',
    '"股票代號 (Symbol)"': 't("col_symbol")',
    '"動作 (Action)"': 't("col_action")',
    '"股數 (Shares)"': 't("col_shares")',
    '"價格 (Price)"': 't("col_price")',
    '"券商 (Broker)"': 't("col_broker")',
    '"手續費 (Fee) [選填]"': 't("col_fee")',
    '"備註 (Note) [選填]"': 't("col_note")',
    '"(手動輸入)"': 't("manual_input")',
    '"選擇預設券商"': 't("default_broker")',
    '"預設券商 (Broker)"': 't("default_broker_2")',
    '"匯入日期 (Date)"': 't("import_date")',
    '"(無)"': 't("no_fee_note")',
    '"成本類型"': 't("cost_type")',
    '"總成本 (Total Cost)"': 't("total_cost")',
    '"平均價格 (Avg Price)"': 't("avg_price")',
    '"預覽轉換後資料"': 't("preview_parsed_data")',
    '"請輸入要修改的紀錄 ID (ID)"': 't("edit_tx_id")',
    'f"正在修改紀錄 ID: {edit_id} ({r[\'action\']} {r[\'symbol\']})"': 't("editing_tx", id=edit_id, act=r["action"], sym=r["symbol"])',
    '"找不到此 ID 的紀錄，請確認 ID 是否正確。"': 't("tx_not_found")'
}

replacements_dividends = {
    '"📊 歷史實際獲得配息/配股統計"': 't("hist_div_stats")',
    '"今年已領股利總額"': 't("div_this_year")',
    '"在途待領股利總額"': 't("div_pending")',
    '"歷年累計總股利"': 't("div_all_time")',
    '["全部"]': '[t("all")]',
    '["按個股聚合"]': '[t("group_by_stock")]',
    '== "全部"': '== t("all")',
    '== "按個股聚合"': '== t("group_by_stock")',
    '"尚無任何配息紀錄"': 't("no_div_records")',
    '"股票代碼"': 't("symbol")',
    '"累計現金配息"': 't("acc_cash_div")',
    '"累計股票配股"': 't("acc_stock_div")',
    'f"共 {len(sym_df)} 筆紀錄"': 't("total_n_records", n=len(sym_df))',
    'f"{int(y)} 年度"': 't("year_y", y=int(y))',
    '"累計現金："': 't("div_acc_cash")',
    '"累計配股："': 't("div_acc_stock")',
    '"現金股利"': 't("div_cash_lbl")',
    '"股票股利"': 't("div_stock_lbl")'
}

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'from i18n import t' not in content and 'import t' not in content:
        content = content.replace('import streamlit as st', 'import streamlit as st\nfrom i18n import t', 1)
        
    for k, v in replacements.items():
        content = content.replace(k, v)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replace_in_file('views/00_dashboard.py', replacements_dashboard)
replace_in_file('views/02_transactions.py', replacements_transactions)
replace_in_file('views/03_dividends.py', replacements_dividends)
print("Replacements complete!")
