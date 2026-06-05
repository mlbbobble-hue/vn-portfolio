text = """
越南股市投資日報 
 2026年06月04日 
 CHEN-YU-HSUAN  您好！ 
...
2nd Floor, Eliteco Building No.18 Tran Hung Dao, Hoang Van Thu Ward, Hong Bang Ward, Hai Phong
"""

import re
def parse_broker_email(text):
    transactions = []
    text_upper = text.upper()
    
    if "投資日報" in text_upper or "BẢN TIN" in text_upper or "NEWSLETTER" in text_upper:
        return transactions
    return ["Should have ignored but didn't"]

print("Result:", parse_broker_email(text))
