import re

with open("views/00_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace MUJI colors in dashboard with Synthwave colors directly
replacements = {
    '#8A9A5B': '#FF2A85', # MUJI Green -> Synthwave Pink
    '#C97A7E': '#9D4EDD', # MUJI Red -> Synthwave Purple
    '#8BA3C7': '#00F0FF', # MUJI Blue (Totals) -> Synthwave Cyan
    '#6D85AB': '#FFFFFF', # MUJI Dark Blue (Line) -> White
    '#C2B8AD': '#00F0FF', # MUJI Connector -> Synthwave Cyan
    '#4A4A4A': '#FFFFFF', # MUJI text -> White
    '#8C8C8C': '#D8B4E2', # MUJI secondary -> Light Purple
    '#E6E1D8': 'rgba(0,0,0,0)', # MUJI Grid -> transparent
    '#F2EDE4': 'rgba(0,0,0,0)', # MUJI Grid -> transparent
    'color_continuous_scale=[(0, "#9D4EDD"), (0.5, "rgba(0,0,0,0)"), (1, "#FF2A85")]': 'color_continuous_scale=[(0, "#9D4EDD"), (0.5, "rgba(20, 18, 38, 0.6)"), (1, "#FF2A85")]'
}

for old, new in replacements.items():
    content = content.replace(old, new)

# specifically hide axes
content = content.replace('yaxis=dict(zeroline=True, zerolinecolor="rgba(0,0,0,0)", gridcolor="rgba(0,0,0,0)")', 'yaxis=dict(visible=False)')
content = content.replace('xaxis=dict(gridcolor="rgba(0,0,0,0)")', 'xaxis=dict(visible=False)')

with open("views/00_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard Synthwave fix success")
