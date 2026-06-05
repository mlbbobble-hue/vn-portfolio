import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """    mail_ids = list(all_mail_ids)
    found = len(mail_ids)
    inserted = 0"""

new1 = """    mail_ids = list(all_mail_ids)
    found = len(mail_ids)
    inserted = 0
    debug_text = "" """

target2 = """                text = extract_text_from_email(msg)
                txns = parse_broker_email(text, date_str, broker)"""

new2 = """                text = extract_text_from_email(msg)
                debug_text = text # 記錄最後一封信的文字內容
                txns = parse_broker_email(text, date_str, broker)"""

target3 = """    mail.logout()
    return {"found": found, "inserted": inserted}"""

new3 = """    mail.logout()
    return {"found": found, "inserted": inserted, "debug_text": debug_text}"""

if target1 in content and target2 in content and target3 in content:
    content = content.replace(target1, new1)
    content = content.replace(target2, new2)
    content = content.replace(target3, new3)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py with debug text")
else:
    print("Targets not found in email_parser.py")
