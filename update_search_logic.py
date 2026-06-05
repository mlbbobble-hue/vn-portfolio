import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """    all_mail_ids = set()
    for domain in domains_to_search:
        status, messages = mail.search(None, f'(UNSEEN FROM "{domain}")')"""

new1 = """    from datetime import datetime
    today_imap = datetime.now().strftime("%d-%b-%Y") # e.g. 04-Jun-2026
    
    all_mail_ids = set()
    for domain in domains_to_search:
        # 改為搜尋「今天」的所有信件，不管是否已讀
        status, messages = mail.search(None, f'(SINCE "{today_imap}" FROM "{domain}")')"""

target2 = """                for t in txns:
                    try:
                        sb_add_transaction(
                            user_id=user_id,
                            date=t["date"],
                            broker=broker,
                            symbol=t["symbol"],
                            action=t["action"],
                            shares=t["shares"],
                            price=t["price"],
                            fee=t.get("fee", 0),
                            note="Auto-synced from Email"
                        )
                        inserted += 1
                    except Exception as e:
                        print(f"Error inserting {t}: {e}")"""

new2 = """                # 為了避免重複匯入，先取得今日已有的交易紀錄
                from supabase_db import sb_get_all_transactions
                try:
                    existing_txns = sb_get_all_transactions(user_id)
                    # 只過濾出今天的
                    if not existing_txns.empty:
                        existing_txns = existing_txns[existing_txns["date"].str.startswith(date_str)]
                except:
                    import pandas as pd
                    existing_txns = pd.DataFrame()
                
                for t in txns:
                    try:
                        # 檢查是否已經存在完全相同的交易紀錄
                        is_duplicate = False
                        if not existing_txns.empty:
                            mask = (
                                (existing_txns["symbol"] == t["symbol"]) &
                                (existing_txns["action"] == t["action"]) &
                                (existing_txns["shares"] == t["shares"]) &
                                (existing_txns["price"] == t["price"])
                            )
                            if mask.any():
                                is_duplicate = True
                                
                        if not is_duplicate:
                            sb_add_transaction(
                                user_id=user_id,
                                date=t["date"],
                                broker=broker,
                                symbol=t["symbol"],
                                action=t["action"],
                                shares=t["shares"],
                                price=t["price"],
                                fee=t.get("fee", 0),
                                note="Auto-synced from Email"
                            )
                            inserted += 1
                    except Exception as e:
                        print(f"Error inserting {t}: {e}")"""

if target1 in content and target2 in content:
    content = content.replace(target1, new1)
    content = content.replace(target2, new2)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py for SINCE search and duplicate prevention")
else:
    print("Targets not found in email_parser.py")
