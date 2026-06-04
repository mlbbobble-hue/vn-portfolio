import re

with open("views/00_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace hardcoded colors for MUJI theme
replacements = {
    'c_color = "#10b981"': 'c_color = "#8A9A5B"',
    'c_color = "#ef4444"': 'c_color = "#C97A7E"',
    
    # Waterfall chart colors
    'decreasing={"marker":{"color":"#ef4444"}}': 'decreasing={"marker":{"color":"#C97A7E"}}',
    'increasing={"marker":{"color":"#10b981"}}': 'increasing={"marker":{"color":"#8A9A5B"}}',
    'totals={"marker":{"color":"#3b82f6", "line": {"color":"#60a5fa", "width":2}}}': 'totals={"marker":{"color":"#8BA3C7", "line": {"color":"#6D85AB", "width":1}}}',
    'connector={"line":{"color":"#475569", "dash":"dot"}}': 'connector={"line":{"color":"#C2B8AD", "dash":"dot"}}',
    'title=dict(text=f"<b>{wf_title}</b>", font=dict(size=18, color="#f8fafc"), x=0.015, y=0.9)': 'title=dict(text=f"<b>{wf_title}</b>", font=dict(size=18, color="#4A4A4A"), x=0.015, y=0.9)',
    'plot_bgcolor="#0f172a"': 'plot_bgcolor="rgba(0,0,0,0)"',
    'paper_bgcolor="#0f172a"': 'paper_bgcolor="rgba(0,0,0,0)"',
    'font=dict(color="#94a3b8")': 'font=dict(color="#8C8C8C")',
    'yaxis=dict(zeroline=True, zerolinecolor="#334155", gridcolor="#1e293b")': 'yaxis=dict(zeroline=True, zerolinecolor="#E6E1D8", gridcolor="#F2EDE4")',
    'xaxis=dict(gridcolor="#1e293b")': 'xaxis=dict(gridcolor="#F2EDE4")',
    
    # Treemap colors
    'color_continuous_scale=[(0, "#ef4444"), (0.5, "#64748b"), (1, "#10b981")]': 'color_continuous_scale=[(0, "#C97A7E"), (0.5, "#E6E1D8"), (1, "#8A9A5B")]',
    'title=dict(\n                    text=f"<b>{title_text}</b>",\n                    font=dict(size=18, color="#f8fafc"),': 'title=dict(\n                    text=f"<b>{title_text}</b>",\n                    font=dict(size=18, color="#4A4A4A"),'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open("views/00_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard rewrite success")
