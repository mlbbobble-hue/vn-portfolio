import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """def run_email_sync(user_id):
    from supabase_db import sb_load_imap_settings
    settings = sb_load_imap_settings(user_id)"""

new1 = """def run_email_sync(user_id, start_date=None):
    from supabase_db import sb_load_imap_settings
    settings = sb_load_imap_settings(user_id)"""

target2 = """    from datetime import datetime
    today_imap = datetime.now().strftime("%d-%b-%Y") # e.g. 04-Jun-2026
    
    all_mail_ids = set()
    for domain in domains_to_search:
        # 改為搜尋「今天」的所有信件，不管是否已讀
        status, messages = mail.search(None, f'(SINCE "{today_imap}" FROM "{domain}")')"""

new2 = """    from datetime import datetime
    if start_date is None:
        start_date = datetime.now()
    since_imap = start_date.strftime("%d-%b-%Y")
    
    all_mail_ids = set()
    for domain in domains_to_search:
        # 根據選定的日期搜尋信件
        status, messages = mail.search(None, f'(SINCE "{since_imap}" FROM "{domain}")')"""

if target1 in content and target2 in content:
    content = content.replace(target1, new1)
    content = content.replace(target2, new2)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py to accept start_date")
else:
    print("Targets not found in email_parser.py")
