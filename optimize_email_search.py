import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    sender_domain = ""
    if broker == "TCBS":
        sender_domain = "@tcbs.com.vn"
    elif broker == "SSI":
        sender_domain = "@ssi.com.vn"
    elif broker == "VNDIRECT":
        sender_domain = "@vndirect.com.vn"
    elif broker == "PHS":
        sender_domain = "@phs.vn"
    elif broker == "ALL (搜尋全部券商)":
        sender_domain = "" # 空字串代表不限制寄件者
        
    if sender_domain:
        status, messages = mail.search(None, f'(UNSEEN FROM "{sender_domain}")')
    else:
        status, messages = mail.search(None, '(UNSEEN)')
        
    if status != "OK":
        return {"found": 0, "inserted": 0}
        
    mail_ids = messages[0].split()"""

new_code = """    domains_to_search = []
    if broker == "TCBS":
        domains_to_search = ["@tcbs.com.vn"]
    elif broker == "SSI":
        domains_to_search = ["@ssi.com.vn"]
    elif broker == "VNDIRECT":
        domains_to_search = ["@vndirect.com.vn"]
    elif broker == "PHS":
        domains_to_search = ["@phs.vn"]
    elif broker == "ALL (搜尋全部券商)":
        domains_to_search = ["@tcbs.com.vn", "@ssi.com.vn", "@vndirect.com.vn", "@phs.vn"]
    
    all_mail_ids = set()
    for domain in domains_to_search:
        status, messages = mail.search(None, f'(UNSEEN FROM "{domain}")')
        if status == "OK":
            ids = messages[0].split()
            all_mail_ids.update(ids)
            
    mail_ids = list(all_mail_ids)"""

if target in content:
    content = content.replace(target, new_code)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py to optimize ALL search")
else:
    print("Target not found in email_parser.py")
