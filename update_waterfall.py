import re

with open("views/00_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """        total_worth = val_cost + val_realized + val_unrealized + val_cash_div + val_stock_div
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="P&L", orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["當前投入本金", "已實現損益", "未實現損益", "現金配息", "配股現值", "總經濟價值"],
            textposition="outside",
            text=[f"{v:,.0f}" for v in [val_cost, val_realized, val_unrealized, val_cash_div, val_stock_div, total_worth]],
            y=[val_cost, val_realized, val_unrealized, val_cash_div, val_stock_div, 0],"""

new_code = """        total_profit = val_realized + val_unrealized + val_cash_div + val_stock_div
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="P&L", orientation="v",
            measure=["relative", "relative", "relative", "relative", "total"],
            x=["已實現損益", "未實現損益", "現金配息", "配股現值", "總投資淨利"],
            textposition="outside",
            text=[f"{v:,.0f}" for v in [val_realized, val_unrealized, val_cash_div, val_stock_div, total_profit]],
            y=[val_realized, val_unrealized, val_cash_div, val_stock_div, 0],"""

if target in content:
    content = content.replace(target, new_code)
    with open("views/00_dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Waterfall chart updated to exclude principal")
else:
    print("Target string not found in 00_dashboard.py")
