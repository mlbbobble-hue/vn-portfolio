import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
from supabase_db import sb_load_imap_settings, sb_add_transaction

def extract_text_from_email(msg):
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
            elif ctype == 'text/html' and 'attachment' not in cdispo:
                try:
                    from bs4 import BeautifulSoup
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    text += BeautifulSoup(html, "html.parser").get_text(separator=' ')
                except:
                    # fallback
                    try:
                        text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
    else:
        try:
            text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    return text

def parse_broker_email(text, date_str, broker_name):
    """
    解析券商的成交回報信件。
    使用 Regex 擷取: 買/賣, 股票代號, 數量, 價格
    """
    transactions = []
    text = text.upper()
    
    # TCBS / SSI 常見關鍵字: "MUA", "BÁN", 加上股號(3碼), 加上數字
    # 這裡實作一個初步的 heuristic 解析器
    
    # 尋找類似: MUA 100 FPT 100,000 或 BÁN FPT 100 100000
    # 我們將文字拆分成多行來尋找
    lines = text.split('\n')
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # 尋找 MUA (BUY) 或是 BÁN/BAN (SELL)
        is_buy = "MUA" in line_clean or "BUY" in line_clean
        is_sell = "BÁN" in line_clean or "BAN" in line_clean or "SELL" in line_clean
        
        if is_buy or is_sell:
            action = "BUY" if is_buy else "SELL"
            
            # 尋找 3 位數的大寫字母作為股票代號
            # 例如: FPT, HPG, VCB
            symbols = re.findall(r'\b[A-Z0-9]{3}\b', line_clean)
            # 過濾掉常見非股票的三字元 (如 VND, MUA, BAN, BUY)
            symbols = [s for s in symbols if s not in ["VND", "MUA", "BAN", "BUY"]]
            
            if not symbols:
                continue
                
            symbol = symbols[0]
            
            # 尋找數字 (包含逗號的數字，例如 10,000)
            # 移除非數字與逗號/點號以外的字元來萃取
            # 例如 "10,000", "100.5", "100"
            nums_str = re.findall(r'\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b|\b\d+\b', line_clean)
            
            # 轉換為 float
            parsed_nums = []
            for n_str in nums_str:
                try:
                    # 判斷是千分位逗號還是小數點。越南文通常 . 是千分位, , 是小數點。
                    # 但在信件裡可能會混用。這裡粗略處理：如果有多個逗號，或是逗號後面是3個數字，當作千分位。
                    clean_n = n_str.replace(',', '').replace('.', '') # 先粗暴拔掉，但如果是有小數點的會出錯。
                    # 更精準的：如果包含逗號，且長度符合 10,000，則移除了逗號。
                    if '.' in n_str and ',' not in n_str:
                        # 可能是 10.5 或 10.000
                        parts = n_str.split('.')
                        if len(parts[-1]) == 3:
                            n_val = float(n_str.replace('.', '')) # 10.000 -> 10000
                        else:
                            n_val = float(n_str)
                    elif ',' in n_str and '.' not in n_str:
                        parts = n_str.split(',')
                        if len(parts[-1]) == 3:
                            n_val = float(n_str.replace(',', '')) # 10,000 -> 10000
                        else:
                            n_val = float(n_str.replace(',', '.'))
                    else:
                        n_val = float(re.sub(r'[^0-9.]', '', n_str.replace(',', '')))
                        
                    if n_val > 0:
                        parsed_nums.append(n_val)
                except:
                    pass
                    
            if len(parsed_nums) >= 2:
                # 假設比較小的數字是股數 (通常 100 的倍數)，比較大的是價格 (幾萬 VND)
                # 這是一個 heuristic
                parsed_nums.sort()
                
                # 如果有找到 >= 100 的數字，我們猜測是股數。
                # 不過，越南股市的股數也是 100 的倍數。價格如果是 10,000 (10k)。
                # 這裡就先大膽假設 [0] 是數量, [1] 是價格 (除非價格非常低)
                shares = parsed_nums[0]
                price = parsed_nums[-1] # 取最大的當價格
                
                # 防呆: 如果價格小於 1000，可能是錯的 (越南股市價格通常 > 1000)
                # 除非是 Penny stock。如果股數也是幾百，那就真的很難分。
                # 若發現有矛盾，我們仍然記錄下來，使用者可以後續在 UI 修改。
                if price < 1000 and shares >= 1000:
                    shares, price = price, shares
                    
                transactions.append({
                    "date": date_str,
                    "symbol": symbol,
                    "action": action,
                    "shares": shares,
                    "price": price,
                    "fee": 0 # 未來可以再優化手續費解析
                })
                
    # 去除完全重複的解析紀錄
    unique_txns = []
    seen = set()
    for t in transactions:
        key = f"{t['symbol']}_{t['action']}_{t['shares']}_{t['price']}"
        if key not in seen:
            seen.add(key)
            unique_txns.append(t)
            
    return unique_txns

def run_email_sync(user_id):
    settings = sb_load_imap_settings(user_id)
    email_user = settings.get("imap_email")
    email_pass = settings.get("imap_password")
    broker = settings.get("broker_name", "TCBS")
    
    if not email_user or not email_pass:
        raise ValueError("尚未設定 Email 或密碼。")
        
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
    except Exception as e:
        raise ValueError(f"登入失敗，請檢查應用程式密碼是否正確。({e})")
        
    mail.select("inbox")
    
    sender_domain = ""
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
        
    mail_ids = messages[0].split()
    found = len(mail_ids)
    inserted = 0
    
    for mid in mail_ids:
        res, msg_data = mail.fetch(mid, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                date_tuple = email.utils.parsedate_tz(msg['Date'])
                if date_tuple:
                    local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                    date_str = local_date.strftime("%Y-%m-%d")
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                
                text = extract_text_from_email(msg)
                txns = parse_broker_email(text, date_str, broker)
                
                for t in txns:
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
                        print(f"Error inserting {t}: {e}")
                        
        # 標記為已讀 (SEEN)
        # 測試階段可以先不標記，方便重複測試。但上線需要。
        mail.store(mid, '+FLAGS', '\\Seen')
                        
    mail.logout()
    return {"found": found, "inserted": inserted}

if __name__ == "__main__":
    # For local testing
    pass
