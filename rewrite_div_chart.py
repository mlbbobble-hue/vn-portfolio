import re

with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    content = f.read()

target = '</div>\n</div>\n""", unsafe_allow_html=True)\n\n        # 5. 渲染 Filter Tabs'

new_code = '''</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # --- MUJI Style Bar Chart ---
        df_div_chart = all_divs[all_divs["ex_date"] != ""].copy()
        df_div_chart["ex_date"] = pd.to_datetime(df_div_chart["ex_date"], errors="coerce")
        df_div_chart = df_div_chart.dropna(subset=["ex_date"])
        df_div_chart["month"] = df_div_chart["ex_date"].dt.strftime("%Y-%m")
        
        df_div_chart["val"] = 0.0
        
        for idx, r in df_div_chart.iterrows():
            if r["type"] == "CASH":
                df_div_chart.at[idx, "val"] = float(r.get("cash_received", 0))
            else:
                sym = r["symbol"]
                curr_price = price_cache.get(sym, 0)
                df_div_chart.at[idx, "val"] = float(r.get("stock_received", 0)) * curr_price
                
        df_monthly = df_div_chart.groupby(["month", "type"])["val"].sum().reset_index()
        df_monthly["type_str"] = df_monthly["type"].map({"CASH": "現金配息", "STOCK": "配股現值"})
        
        import plotly.express as px
        fig_bar = px.bar(df_monthly, x="month", y="val", color="type_str", 
                         color_discrete_map={"現金配息": "#D9C589", "配股現值": "#A68A64"},
                         barmode="stack")
        
        lang = st.session_state.get("lang", "zh")
        bar_title = "每月被動收入趨勢" if lang == "zh" else "Xu hướng thu nhập thụ động hàng tháng"
        
        fig_bar.update_layout(
            title=dict(text=f"<b>{bar_title}</b>", font=dict(size=16, color="#4A4A4A")),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20, l=40, r=20),
            height=280,
            yaxis=dict(title="", gridcolor="#E6E1D8", zeroline=False),
            xaxis=dict(title="", gridcolor="rgba(0,0,0,0)", zeroline=False, type='category'),
            legend=dict(title="", orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(color="#4A4A4A"))
        )
        st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 24px;'>", unsafe_allow_html=True)
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 5. 渲染 Filter Tabs'''

if target in content:
    content = content.replace(target, new_code)
    
    # Also replace hardcoded dark colors
    content = content.replace("color: #94a3b8;", "color: #8C8C8C;")
    content = content.replace("color: #cbd5e1;", "color: #8C8C8C;")
    content = content.replace("color: #10b981;", "color: #8A9A5B;")
    content = content.replace("color: #f59e0b;", "color: #D9C589;")
    
    with open("views/03_dividends.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Dividends rewrite success")
else:
    print("Cannot find target string")
