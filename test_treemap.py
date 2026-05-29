import pandas as pd
import plotly.express as px

df_plot = pd.DataFrame({
    'symbol': ['CII', 'FPT', 'CII424002', 'MBB', 'OCB', 'MSB', 'HPG_WFT', 'BID'],
    'market_value': [42.36, 16.52, 16.35, 11.57, 9.12, 3.56, 0.36, 0.16],
    'roi_pct': [-1.68, 6.95, 0.0, 113.44, 11.0, 55.3, 6.95, 11.01]
})

def get_category(roi):
    if roi >= 50: return "獲利翻倍"
    if roi > 0: return "穩定獲利"
    if roi < 0: return "微幅虧損"
    return "平盤"

df_plot["performance"] = df_plot["roi_pct"].apply(get_category)
color_map = {
    "獲利翻倍": "#059669", # 深綠
    "穩定獲利": "#34d399", # 淺綠
    "微幅虧損": "#f87171", # 淺紅
    "平盤": "#94a3b8",      # 灰
    "(?)": "#333333"
}

fig = px.treemap(
    df_plot,
    path=[px.Constant("我的投資組合"), "symbol"],
    values="market_value",
    color="performance",
    color_discrete_map=color_map,
    custom_data=["roi_pct"]
)

fig.update_layout(
    height=500,
    margin=dict(t=20, b=20, l=0, r=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white") # for text inside
)

fig.update_traces(
    texttemplate="<b>%{label}</b><br>%{percentParent:.2%}",
    hovertemplate="<b>%{label}</b><br>持股比例: %{percentParent:.2%}<br>預估損益: %{customdata[0]:+.2f}%<extra></extra>",
    textfont=dict(color="white", size=16),
    marker=dict(line=dict(width=2, color='white')) # adds spacing between boxes
)

# Test if it renders
print(fig.to_json()[:200])
