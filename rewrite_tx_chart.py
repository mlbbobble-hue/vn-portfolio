import re

with open("views/02_transactions.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    else:
        fc1, fc2, fc3 = st.columns(3)"""

new_code = """    else:
        # --- MUJI Style Area Chart ---
        df_chart = all_txns.copy()
        df_chart["date"] = pd.to_datetime(df_chart["date"])
        df_chart = df_chart.sort_values(["date", "id"])
        
        cumulative_cost = []
        current_cost = 0.0
        
        for _, row in df_chart.iterrows():
            amount = float(row["shares"]) * float(row["price"])
            if row["action"] == "BUY":
                current_cost += amount + float(row["fee"])
            else:
                current_cost -= (amount - float(row["fee"]))
            cumulative_cost.append(current_cost)
            
        df_chart["cumulative_cost"] = cumulative_cost
        
        import plotly.express as px
        fig_area = px.area(df_chart, x="date", y="cumulative_cost")
        fig_area.update_traces(line_color="#8BA3C7", fillcolor="rgba(139, 163, 199, 0.4)")
        
        lang = st.session_state.get("lang", "zh")
        a_title = "投入資金累積趨勢" if lang == "zh" else "Xu hướng vốn đầu tư"
        
        fig_area.update_layout(
            title=dict(text=f"<b>{a_title}</b>", font=dict(size=16, color="#4A4A4A")),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20, l=40, r=20),
            height=280,
            yaxis=dict(title="", gridcolor="#E6E1D8", zeroline=False),
            xaxis=dict(title="", gridcolor="rgba(0,0,0,0)", zeroline=False)
        )
        st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)
        
        fc1, fc2, fc3 = st.columns(3)"""

if target in content:
    content = content.replace(target, new_code)
    with open("views/02_transactions.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Transactions rewrite success")
else:
    print("Cannot find target string")
