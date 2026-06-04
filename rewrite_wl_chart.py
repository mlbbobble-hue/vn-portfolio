import re

with open("views/04_watchlist.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    if wl.empty:
        st.info(t("no_watchlist"))
    else:
        st.subheader(t("watching_count", n=len(wl)))"""

new_code = """    if wl.empty:
        st.info(t("no_watchlist"))
    else:
        st.subheader(t("watching_count", n=len(wl)))
        
        # --- MUJI Style Gauge Charts ---
        import plotly.graph_objects as go
        
        gauge_data = []
        for _, item in wl.iterrows():
            sym = item["symbol"]
            cur_price = price_map.get(sym,{}).get("price",0)
            target = item.get("target_price") or 0
            if target > 0 and cur_price > 0:
                dist_pct = (cur_price - target) / target * 100
                if dist_pct >= 0:
                    gauge_val = max(0, 100 - dist_pct)
                else:
                    gauge_val = 100
                gauge_data.append((sym, cur_price, target, gauge_val))
                
        if gauge_data:
            gauge_data.sort(key=lambda x: -x[3])
            top_gauges = gauge_data[:3]
            
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(len(top_gauges))
            
            for i, (sym, cur_price, target, g_val) in enumerate(top_gauges):
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = g_val,
                    number = {'suffix': "%", 'font': {'size': 24, 'color': '#4A4A4A'}},
                    title = {'text': f"<b>{sym}</b><br><span style='font-size:0.8em;color:#8C8C8C'>Target: {target:,.0f}</span>", 'font': {'size': 16, 'color': '#4A4A4A'}},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#E6E1D8", 'visible': False},
                        'bar': {'color': "#8A9A5B" if g_val >= 90 else "#D9C589"},
                        'bgcolor': "#F2EDE4",
                        'borderwidth': 0,
                        'shape': "angular"
                    }
                ))
                fig_gauge.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=30, b=10, l=10, r=10),
                    height=200
                )
                with cols[i]:
                    st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); text-align:center;'>", unsafe_allow_html=True)
                    st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
                    st.markdown(f"<div style='font-size:14px;color:#8C8C8C;'>目前市價: {cur_price:,.0f}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
        st.markdown("<br>", unsafe_allow_html=True)"""

if target in content:
    content = content.replace(target, new_code)
    
    # Replace hardcoded dark colors
    content = content.replace("#34d399", "#8A9A5B")
    content = content.replace("#fbbf24", "#D9C589")
    content = content.replace("#94a3b8", "#8C8C8C")
    content = content.replace("#f87171", "#C97A7E")
    content = content.replace("#64748b", "#A6A6A6")
    
    with open("views/04_watchlist.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Watchlist rewrite success")
else:
    print("Cannot find target string")
