import re

# 01_portfolio.py
with open("views/01_portfolio.py", "r", encoding="utf-8") as f:
    c1 = f.read()
repl1 = {
    'broker_colors = ["#8A9A5B", "#8BA3C7", "#D9C589", "#A68A64", "#C97A7E", "#B0A8B9"]': 'broker_colors = ["#00FF41", "#00F0FF", "#FEE715", "#FF007F", "#B026FF", "#FF8C00"]',
    "line=dict(color='#FFFFFF', width=1)": "line=dict(color='#09090B', width=2)",
    'color="#4A4A4A"': 'color="#E0F7FA"',
    'color="#8C8C8C"': 'color="#00F0FF"',
    "color='#8C8C8C'": "color='#00F0FF'"
}
for old, new in repl1.items(): c1 = c1.replace(old, new)
with open("views/01_portfolio.py", "w", encoding="utf-8") as f: f.write(c1)

# 02_transactions.py
with open("views/02_transactions.py", "r", encoding="utf-8") as f:
    c2 = f.read()
repl2 = {
    'line_color="#8BA3C7"': 'line_color="#00F0FF"',
    'fillcolor="rgba(139, 163, 199, 0.4)"': 'fillcolor="rgba(0, 240, 255, 0.4)"',
    'color="#4A4A4A"': 'color="#E0F7FA"',
    'gridcolor="#E6E1D8"': 'gridcolor="rgba(0, 240, 255, 0.2)"'
}
for old, new in repl2.items(): c2 = c2.replace(old, new)
with open("views/02_transactions.py", "w", encoding="utf-8") as f: f.write(c2)

# 03_dividends.py
with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    c3 = f.read()
repl3 = {
    '#D9C589': '#FEE715',
    '#A68A64': '#FF007F',
    '#4A4A4A': '#E0F7FA',
    '#E6E1D8': 'rgba(0, 240, 255, 0.2)',
    '#8C8C8C': '#00F0FF',
    '#8A9A5B': '#00FF41'
}
for old, new in repl3.items(): c3 = c3.replace(old, new)
with open("views/03_dividends.py", "w", encoding="utf-8") as f: f.write(c3)

# 04_watchlist.py
with open("views/04_watchlist.py", "r", encoding="utf-8") as f:
    c4 = f.read()
repl4 = {
    '#4A4A4A': '#E0F7FA',
    '#8C8C8C': '#00F0FF',
    '#E6E1D8': 'rgba(0, 240, 255, 0.2)',
    '#8A9A5B': '#00FF41',
    '#D9C589': '#FEE715',
    '#C97A7E': '#FF007F',
    '#A6A6A6': '#64748b',
    '#F2EDE4': '#09090B'
}
for old, new in repl4.items(): c4 = c4.replace(old, new)
with open("views/04_watchlist.py", "w", encoding="utf-8") as f: f.write(c4)

print("All Cyberpunk scripts applied!")
