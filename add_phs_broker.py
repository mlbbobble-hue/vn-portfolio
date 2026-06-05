import re

with open("views/05_settings.py", "r", encoding="utf-8") as f:
    content = f.read()

target = 'broker_options = ["TCBS", "SSI", "VNDIRECT", "Other"]'
new_code = 'broker_options = ["TCBS", "SSI", "VNDIRECT", "PHS", "ALL (搜尋全部券商)"]'

if target in content:
    content = content.replace(target, new_code)
    with open("views/05_settings.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated 05_settings.py")
else:
    print("Target not found in 05_settings.py")
