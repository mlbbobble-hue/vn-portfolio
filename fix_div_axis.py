import re

with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the invalid gridcolor argument
content = content.replace('yaxis=dict(title="", gridcolor="visible=False", zeroline=False)', 'yaxis=dict(visible=False)')
# Also fix xaxis if it has anything similar
content = content.replace('xaxis=dict(title="", gridcolor="rgba(0,0,0,0)", zeroline=False, type=\'category\')', 'xaxis=dict(visible=False)')

with open("views/03_dividends.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Dividend chart axis fixed")
