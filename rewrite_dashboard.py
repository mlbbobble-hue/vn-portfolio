import re

with open("views/00_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    st.markdown(f'''
    <div class="cathay-card" style="background: {c_bg}; border-left: 6px solid {c_color}; padding: 20px; text-align: left; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); margin-bottom: 20px;">
        <div style="font-size: 14px; color: #94a3b8; margin-bottom: 12px;">{t("unrealized_pl")}</div>
        <div style="font-size: 24px; font-weight: bold; color: {c_color}; margin-bottom: 8px;">{amount_text}</div>
        <div style="font-size: 14px; font-weight: bold; color: {c_color};">{pct_text}</div>
    </div>
    ''', unsafe_allow_html=True)"""

new_code = """    st.markdown(f'''
    <div class="cathay-card" style="background: {c_bg}; border-left: 6px solid {c_color}; padding: 20px; text-align: left; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); margin-bottom: 20px;">
        <div style="font-size: 14px; color: #94a3b8; margin-bottom: 12px;">{t("unrealized_pl")}</div>
        <div style="font-size: 24px; font-weight: bold; color: {c_color}; margin-bottom: 8px;">{amount_text}</div>
        <div style="font-size: 14px; font-weight: bold; color: {c_color};">{pct_text}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 2.5 瀑布圖 (P&L Waterfall Chart)
    if not is_loading_prices and not holdings.empty:
        import plotly.graph_objects as go
        from datetime import date
        
        total_realized_pl = get_total_realized_pl()
        total_cash_div = 0.0
        total_stock_div_val = 0.0
        
        _, _, div_details = compute_received_dividends()
        if div_details:
            price_cache_df = get_price_cache()
            price_cache = price_cache_df.set_index("symbol")["price"].to_dict() if not price_cache_df.empty else {}
            
            for div in div_details:
                pay_date = div.get("pay_date", "")
                is_done = False
                if pay_date and pd.notnull(pay_date) and str(pay_date).strip():
                    try:
                        pdt = pd.to_datetime(pay_date).date()
                        is_done = pdt <= date.today()
                    except:
                        pass
                if is_done:
                    if div["type"] == "CASH":
                        total_cash_div += div.get("cash_received", 0)
                    elif div["type"] == "STOCK":
                        sym = div["symbol"]
                        curr_price = price_cache.get(sym, 0)
                        total_stock_div_val += div.get("stock_received", 0) * curr_price
                        
        divisor = EXCHANGE_RATE if show_in_twd else 1
        val_cost = total_cost / divisor
        val_realized = total_realized_pl / divisor
        val_unrealized = total_unrealized / divisor
        val_cash_div = total_cash_div / divisor
        val_stock_div = total_stock_div_val / divisor
        total_worth = val_cost + val_realized + val_unrealized + val_cash_div + val_stock_div
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="P&L", orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["當前投入本金", "已實現損益", "未實現損益", "現金配息", "配股現值", "總經濟價值"],
            textposition="outside",
            text=[f"{v:,.0f}" for v in [val_cost, val_realized, val_unrealized, val_cash_div, val_stock_div, total_worth]],
            y=[val_cost, val_realized, val_unrealized, val_cash_div, val_stock_div, 0],
            connector={"line":{"color":"#475569", "dash":"dot"}},
            decreasing={"marker":{"color":"#ef4444"}},
            increasing={"marker":{"color":"#10b981"}},
            totals={"marker":{"color":"#3b82f6", "line": {"color":"#60a5fa", "width":2}}}
        ))
        
        lang = st.session_state.get("lang", "zh")
        wf_title = "損益瀑布圖 (P&L Waterfall)" if lang == "zh" else "Biểu đồ Thác nước Lãi/Lỗ"
        
        fig_waterfall.update_layout(
            title=dict(text=f"<b>{wf_title}</b>", font=dict(size=18, color="#f8fafc"), x=0.015, y=0.9),
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font=dict(color="#94a3b8"),
            margin=dict(t=60, b=40, l=40, r=40),
            height=420,
            showlegend=False,
            yaxis=dict(zeroline=True, zerolinecolor="#334155", gridcolor="#1e293b"),
            xaxis=dict(gridcolor="#1e293b")
        )
        st.plotly_chart(fig_waterfall, use_container_width=True, config={'displayModeBar': False})
"""

if target in content:
    content = content.replace(target, new_code)
    with open("views/00_dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Replacement success!")
else:
    print("Cannot find target string")
