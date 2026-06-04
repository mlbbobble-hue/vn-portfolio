import re

# 00_dashboard.py
with open("views/00_dashboard.py", "r", encoding="utf-8") as f:
    c0 = f.read()
repl0 = {
    '#00FF41': '#FF2A85', # Cyber green -> Synthwave Pink
    '#FF007F': '#9D4EDD', # Cyber Pink -> Synthwave Purple
    '#00F0FF': '#00F0FF', # Cyber Cyan -> keep Cyan
    '#E0F7FA': '#FFFFFF', # Cyber White -> pure white
    'gridcolor="rgba(0,240,255,0.1)"': 'visible=False',
    'zerolinecolor="#00F0FF"': 'visible=False',
    'xaxis=dict(gridcolor="rgba(0,240,255,0.1)")': 'xaxis=dict(visible=False)',
    'yaxis=dict(zeroline=True, visible=False)': 'yaxis=dict(visible=False)' # avoid duplication
}
for old, new in repl0.items(): c0 = c0.replace(old, new)
with open("views/00_dashboard.py", "w", encoding="utf-8") as f: f.write(c0)

# 01_portfolio.py
with open("views/01_portfolio.py", "r", encoding="utf-8") as f:
    c1 = f.read()
repl1 = {
    'broker_colors = ["#00FF41", "#00F0FF", "#FEE715", "#FF007F", "#B026FF", "#FF8C00"]': 'broker_colors = ["#00F0FF", "#FF2A85", "#9D4EDD", "#FEE715", "#B026FF", "#FF8C00"]',
    'hole=0.65': 'hole=0.8',
    'width=2': 'width=0' # no borders on donuts
}
for old, new in repl1.items(): c1 = c1.replace(old, new)
with open("views/01_portfolio.py", "w", encoding="utf-8") as f: f.write(c1)

# 02_transactions.py
with open("views/02_transactions.py", "r", encoding="utf-8") as f:
    c2 = f.read()
repl2 = {
    'line_color="#00F0FF"': 'line_color="#FF2A85", line_shape="spline"',
    'fillcolor="rgba(0, 240, 255, 0.4)"': 'fillcolor="rgba(255, 42, 133, 0.2)"',
    'gridcolor="rgba(0, 240, 255, 0.2)"': 'visible=False',
    'color="#E0F7FA"': 'color="#FFFFFF"'
}
for old, new in repl2.items(): c2 = c2.replace(old, new)
with open("views/02_transactions.py", "w", encoding="utf-8") as f: f.write(c2)

# 03_dividends.py
with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    c3 = f.read()
repl3 = {
    '#FEE715': '#00F0FF', # Cash -> Cyan
    'rgba(0, 240, 255, 0.2)': 'visible=False',
    'gridcolor=visible=False': 'visible=False',
    'xaxis=dict(title="", visible=False, zeroline=False, type=\'category\')': 'xaxis=dict(visible=False)'
}
for old, new in repl3.items(): c3 = c3.replace(old, new)
with open("views/03_dividends.py", "w", encoding="utf-8") as f: f.write(c3)

# 04_watchlist.py
with open("views/04_watchlist.py", "r", encoding="utf-8") as f:
    c4 = f.read()
repl4 = {
    '#00FF41': '#FF2A85',
    '#FEE715': '#9D4EDD',
    '#00F0FF': '#D8B4E2',
    'rgba(0, 240, 255, 0.2)': 'rgba(255,255,255,0.05)',
    'tickwidth\': 1': 'tickwidth\': 0',
    '#181825': 'rgba(157, 78, 221, 0.1)',
    '#E0F7FA': '#FFFFFF'
}
for old, new in repl4.items(): c4 = c4.replace(old, new)
with open("views/04_watchlist.py", "w", encoding="utf-8") as f: f.write(c4)

print("Synthwave scripts applied!")
