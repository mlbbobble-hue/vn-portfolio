import re

with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    content = f.read()

# We need to replace the section starting at line 72 up to line 118 with the new logic.
new_code = """        # 3. 計算 Dividend Summary Cards 數據
        from db_router import get_price_cache
        price_cache_df = get_price_cache()
        price_cache = price_cache_df.set_index("symbol")["price"].to_dict() if not price_cache_df.empty else {}

        this_year = date.today().year
        
        # Cash Div
        total_received_this_year = 0.0
        total_pending = 0.0
        total_received_all_time = 0.0
        
        # Stock Div (Current Value)
        total_stock_val_this_year = 0.0
        total_pending_stock_val = 0.0
        total_stock_val_all_time = 0.0
        
        if not merged_divs.empty:
            merged_divs["ex_year"] = pd.to_datetime(merged_divs["ex_date"], errors="coerce").dt.year
            for _, row in merged_divs.iterrows():
                pay_date = row.get("pay_date", "")
                is_done = False
                p_year = 0
                if pay_date and pd.notnull(pay_date) and str(pay_date).strip():
                    try:
                        pdt = pd.to_datetime(pay_date).date()
                        is_done = pdt <= date.today()
                        p_year = pdt.year
                    except:
                        pass
                        
                if row["type"] == "CASH":
                    amt = row.get("cash_received", 0)
                    if is_done:
                        total_received_all_time += amt
                        if p_year == this_year:
                            total_received_this_year += amt
                    else:
                        total_pending += amt
                elif row["type"] == "STOCK":
                    shares_amt = row.get("stock_received", 0)
                    sym = row["symbol"]
                    current_price = price_cache.get(sym, 0)
                    stock_val = shares_amt * current_price
                    
                    if is_done:
                        total_stock_val_all_time += stock_val
                        if p_year == this_year:
                            total_stock_val_this_year += stock_val
                    else:
                        total_pending_stock_val += stock_val

        # 4. 渲染 Summary Cards
        st.markdown(f\"\"\"
<div style="display: flex; gap: 16px; margin-bottom: 16px;">
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(16, 185, 129, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #10b981;">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">💰 今年累計領取配息 (Cash Div)</div>
        <div style="color: #10b981; font-size: 24px; font-weight: 700;">+{total_received_this_year:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(251, 191, 36, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #fbbf24;">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">⏳ 即將入帳配息 (Pending Cash)</div>
        <div style="color: #fbbf24; font-size: 24px; font-weight: 700;">+{total_pending:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(248, 250, 252, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #f8fafc;">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">📈 歷史累計配息 (All-time Cash)</div>
        <div style="color: #f8fafc; font-size: 24px; font-weight: 700;">+{total_received_all_time:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
</div>
<div style="display: flex; gap: 16px; margin-bottom: 24px;">
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #3b82f6;">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">🎁 今年領取配股現值 (Stock Div Value)</div>
        <div style="color: #3b82f6; font-size: 24px; font-weight: 700;">+{total_stock_val_this_year:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(168, 85, 247, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #a855f7;">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">⏳ 即將發放配股現值 (Pending Stock)</div>
        <div style="color: #a855f7; font-size: 24px; font-weight: 700;">+{total_pending_stock_val:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
    <div style="flex: 1; background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid rgba(236, 72, 153, 0.3); box-shadow: var(--shadow-soft); border-left: 4px solid #ec4899;">
        <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">💎 歷史累計配股現值 (All-time Stock)</div>
        <div style="color: #ec4899; font-size: 24px; font-weight: 700;">+{total_stock_val_all_time:,.0f} <span style="font-size:14px;">VNĐ</span></div>
    </div>
</div>
\"\"\", unsafe_allow_html=True)"""

target_start = '        # 3. 計算 Dividend Summary Cards 數據'
target_end = '\"\"\", unsafe_allow_html=True)'

start_idx = content.find(target_start)
end_idx = content.find(target_end, start_idx) + len(target_end)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_code + content[end_idx:]
    with open("views/03_dividends.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Replacement success!")
else:
    print("Cannot find target strings")
