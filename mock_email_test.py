import os
from datetime import datetime
from email_parser import parse_broker_email
from supabase_db import _table, sb_add_transaction

def run_mock_email():
    # 1. Get the user ID
    res = _table("users_approval").select("user_id").limit(1).execute()
    if not res.data:
        print("Error: No users found in database.")
        return
        
    user_id = res.data[0]["user_id"]
    print(f"Using user_id: {user_id}")
    
    # 2. Fake Email Content
    today_str = datetime.now().strftime("%Y-%m-%d")
    fake_email_text = f"""
    Thông báo khớp lệnh (Matched order notification)
    
    Kính gửi Quý khách,
    
    Lệnh giao dịch của Quý khách đã được khớp với chi tiết như sau:
    MUA 100 FPT giá 135,000 VND
    
    Trân trọng,
    TCBS
    """
    
    print("Fake Email Content:")
    print(fake_email_text)
    
    # 3. Parse it
    print("Parsing email...")
    txns = parse_broker_email(fake_email_text, today_str, "TCBS")
    
    if not txns:
        print("Parser failed to extract transaction.")
        return
        
    print(f"Extracted transactions: {txns}")
    
    # 4. Insert into database
    for t in txns:
        try:
            sb_add_transaction(
                user_id=user_id,
                date=t["date"],
                broker="TCBS",
                symbol=t["symbol"],
                action=t["action"],
                shares=t["shares"],
                price=t["price"],
                fee=0,
                note="Mock Email Auto-synced"
            )
            print(f"Success! Inserted {t['action']} {t['shares']} shares of {t['symbol']} at {t['price']}")
        except Exception as e:
            print(f"Failed to insert: {e}")

if __name__ == "__main__":
    run_mock_email()
