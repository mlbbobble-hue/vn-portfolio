import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target = r"symbols = re.findall(r'\b[A-Z0-9]{3}\b', line_clean)"
new_code = r"symbols = re.findall(r'\b[A-Z]{3}\b', line_clean)"

if target in content:
    content = content.replace(target, new_code)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed regex in email_parser.py")
else:
    print("Target not found in email_parser.py")
