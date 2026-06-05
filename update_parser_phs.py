import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    if broker == "TCBS":
        sender_domain = "@tcbs.com.vn"
    elif broker == "SSI":
        sender_domain = "@ssi.com.vn"
    elif broker == "VNDIRECT":
        sender_domain = "@vndirect.com.vn\""""

new_code = """    if broker == "TCBS":
        sender_domain = "@tcbs.com.vn"
    elif broker == "SSI":
        sender_domain = "@ssi.com.vn"
    elif broker == "VNDIRECT":
        sender_domain = "@vndirect.com.vn"
    elif broker == "PHS":
        sender_domain = "@phs.vn"
    elif broker == "ALL (搜尋全部券商)":
        sender_domain = "" # 空字串代表不限制寄件者"""

if target in content:
    content = content.replace(target, new_code)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py")
else:
    print("Target not found in email_parser.py")
