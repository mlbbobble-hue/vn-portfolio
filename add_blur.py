import re

with open("theme.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """/* 白色卡片 */
.card, [data-testid="metric-container"], .cathay-card {
    background-color: var(--cathay-white) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-soft);
}"""

new_code = """/* 毛玻璃卡片 */
.card, [data-testid="metric-container"], .cathay-card {
    background-color: var(--cathay-white) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-soft);
}"""

if target in content:
    content = content.replace(target, new_code)
    with open("theme.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("backdrop-filter added")
else:
    print("Target not found")
