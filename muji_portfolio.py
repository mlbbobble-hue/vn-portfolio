import re

with open("views/01_portfolio.py", "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    'broker_colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6"]': 'broker_colors = ["#8A9A5B", "#8BA3C7", "#D9C589", "#A68A64", "#C97A7E", "#B0A8B9"]',
    "line=dict(color='#0f172a', width=2)": "line=dict(color='#FFFFFF', width=1)",
    'font=dict(size=16, color="#f8fafc", family="Inter, sans-serif")': 'font=dict(size=16, color="#4A4A4A")',
    'font=dict(color="#94a3b8", size=12)': 'font=dict(color="#8C8C8C", size=12)',
    "outsidetextfont=dict(color='#cbd5e1', size=12)": "outsidetextfont=dict(color='#8C8C8C', size=12)",
    "border: 1px solid rgba(255,255,255,0.05);": "border: 1px solid var(--border-color);",
    'color="#f8fafc"': 'color="#4A4A4A"'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open("views/01_portfolio.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Portfolio rewrite success")
