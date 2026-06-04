import re

with open("views/01_portfolio.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """st.markdown("<br>", unsafe_allow_html=True)
st.subheader(t("detail_holdings"))"""

new_code = """
if not portfolio_df.empty:
    df_for_charts = portfolio_df[portfolio_df["market_value"] > 0]
    
    if not df_for_charts.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        chart_col1, chart_col2 = st.columns(2)
        
        # --- Broker Distribution ---
        broker_mkt_val = {}
        for _, r in df_for_charts.iterrows():
            cp = r.get("current_price", 0)
            bb = r.get("broker_breakdown", {})
            if isinstance(bb, dict):
                for b_name, b_shares in bb.items():
                    broker_mkt_val[b_name] = broker_mkt_val.get(b_name, 0) + (b_shares * cp)
        
        broker_mkt_val = {k: v for k, v in broker_mkt_val.items() if v > 0}
        
        if broker_mkt_val:
            b_labels = list(broker_mkt_val.keys())
            b_values = list(broker_mkt_val.values())
            
            lang = st.session_state.get("lang", "zh")
            b_title = "券商資產分佈" if lang == "zh" else "Phân bổ CTCK"
            
            # Premium color palette
            broker_colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6"]
            
            fig_broker = go.Figure(data=[go.Pie(
                labels=b_labels, values=b_values,
                hole=0.65,
                marker=dict(colors=broker_colors, line=dict(color='#0f172a', width=2)),
                textinfo='percent',
                textposition='inside',
                insidetextfont=dict(color='white', size=13, family="Inter, sans-serif"),
                hovertemplate="<b>%{label}</b><br>₫%{value:,.0f}<br>%{percent}<extra></extra>"
            )])
            
            fig_broker.update_layout(
                title=dict(text=f"<b>{b_title}</b>", font=dict(size=16, color="#f8fafc", family="Inter, sans-serif"), x=0.5, y=0.95),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=50, b=40, l=20, r=20),
                height=320,
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(color="#94a3b8", size=12))
            )
            with chart_col1:
                st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); box-shadow: var(--shadow-soft);'>", unsafe_allow_html=True)
                st.plotly_chart(fig_broker, use_container_width=True, config={'displayModeBar': False})
                st.markdown("</div>", unsafe_allow_html=True)
        
        # --- Asset Allocation ---
        a_labels = df_for_charts["symbol"].tolist()
        a_values = df_for_charts["market_value"].tolist()
        
        lang = st.session_state.get("lang", "zh")
        a_title = "持股資產配置" if lang == "zh" else "Phân bổ Tài sản"
        
        asset_colors = px.colors.qualitative.Pastel + px.colors.qualitative.Set3
        
        fig_asset = go.Figure(data=[go.Pie(
            labels=a_labels, values=a_values,
            hole=0.65,
            marker=dict(colors=asset_colors, line=dict(color='#0f172a', width=2)),
            textinfo='label+percent',
            textposition='outside',
            insidetextfont=dict(color='white', size=12),
            outsidetextfont=dict(color='#cbd5e1', size=12),
            hovertemplate="<b>%{label}</b><br>₫%{value:,.0f}<br>%{percent}<extra></extra>"
        )])
        
        fig_asset.update_layout(
            title=dict(text=f"<b>{a_title}</b>", font=dict(size=16, color="#f8fafc", family="Inter, sans-serif"), x=0.5, y=0.95),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=50, b=40, l=40, r=40),
            height=320,
            showlegend=False
        )
        
        with chart_col2:
            st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); box-shadow: var(--shadow-soft);'>", unsafe_allow_html=True)
            st.plotly_chart(fig_asset, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.subheader(t("detail_holdings"))"""

if target in content:
    content = content.replace(target, new_code)
    with open("views/01_portfolio.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Replacement success!")
else:
    print("Cannot find target string")
