import re

with open("views/00_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    'c_color = "#8A9A5B"': 'c_color = "#00FF41"',
    'c_color = "#C97A7E"': 'c_color = "#FF007F"',
    'decreasing={"marker":{"color":"#C97A7E"}}': 'decreasing={"marker":{"color":"#FF007F", "line": {"color": "#FF007F", "width": 1}}}',
    'increasing={"marker":{"color":"#8A9A5B"}}': 'increasing={"marker":{"color":"#00FF41", "line": {"color": "#00FF41", "width": 1}}}',
    'totals={"marker":{"color":"#8BA3C7", "line": {"color":"#6D85AB", "width":1}}}': 'totals={"marker":{"color":"#00F0FF", "line": {"color":"#E0F7FA", "width":2}}}',
    'connector={"line":{"color":"#C2B8AD", "dash":"dot"}}': 'connector={"line":{"color":"#00F0FF", "dash":"dot"}}',
    'font=dict(size=18, color="#4A4A4A")': 'font=dict(size=18, color="#E0F7FA")',
    'font=dict(color="#8C8C8C")': 'font=dict(color="#00F0FF")',
    'yaxis=dict(zeroline=True, zerolinecolor="#E6E1D8", gridcolor="#F2EDE4")': 'yaxis=dict(zeroline=True, zerolinecolor="#00F0FF", gridcolor="rgba(0,240,255,0.1)")',
    'xaxis=dict(gridcolor="#F2EDE4")': 'xaxis=dict(gridcolor="rgba(0,240,255,0.1)")',
    'color_continuous_scale=[(0, "#C97A7E"), (0.5, "#E6E1D8"), (1, "#8A9A5B")]': 'color_continuous_scale=[(0, "#FF007F"), (0.5, "#181825"), (1, "#00FF41")]'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open("views/00_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard cyberpunk rewrite success")
