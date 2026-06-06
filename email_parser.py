import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
from supabase_db import sb_load_imap_settings, sb_add_transaction

import io
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

def extract_text_from_email(msg):
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            
            # 處理文字與 HTML
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    text += part.get_payload(decode=True).decode('utf-8', errors='ignore') + "\n"
                except:
                    pass
            elif ctype == 'text/html' and 'attachment' not in cdispo:
                try:
                    from bs4 import BeautifulSoup
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    text += BeautifulSoup(html, "html.parser").get_text(separator=' ') + "\n"
                except:
                    try:
                        text += part.get_payload(decode=True).decode('utf-8', errors='ignore') + "\n"
                    except:
                        pass
            
            # 處理 PDF 附件 (券商的交易回報通常是 PDF)
            elif 'pdf' in ctype.lower() or part.get_filename() and part.get_filename().lower().endswith('.pdf'):
                if PdfReader:
                    try:
                        pdf_data = part.get_payload(decode=True)
                        if pdf_data:
                            reader = PdfReader(io.BytesIO(pdf_data))
                            for page in reader.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text + "\n"
                    except Exception as e:
                        print(f"Error parsing PDF attachment: {e}")
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
    text_upper = text.upper()
    
    # 忽略市場報告/日報，避免誤判
    if "投資日報" in text_upper or "BẢN TIN" in text_upper or "NEWSLETTER" in text_upper:
        return transactions
    
    lines = text.split('\n')
    
    for line in lines:
        line_clean = line.strip().upper()
        if not line_clean:
            continue
            
        # 判斷買賣，放寬 boundary 以支援 MUA(BUY) 連在一起的情況
        is_buy = bool(re.search(r'\b(MUA|BUY)\b|MUA\(BUY\)', line_clean))
        is_sell = bool(re.search(r'\b(BÁN|BAN|SELL)\b|BÁN\(SELL\)|BAN\(SELL\)', line_clean))
        
        if is_buy or is_sell:
            action = "BUY" if is_buy else "SELL"
            
            # 擷取連續3個大寫英文字母，前後不能有大寫英文字母 (解決 SCS05/06/2026 黏在一起的問題)
            symbols = re.findall(r'(?<![A-Z])[A-Z]{3}(?![A-Z])', line_clean)
            # 過濾掉常見的非股票代號3字母
            ignore_list = {"VND", "USD", "THU", "BAN", "HAI", "HON", "DAO", "VAN", "WAR", "HCM", "HNX", "OTC", "UPC", "MUA", "BUY", "GIA", "PHI", "TNH", "CPN", "JSC", "THE", "STT"}
            symbols = [s for s in symbols if s not in ignore_list]
            
            if not symbols:
                continue
                
            symbol = symbols[0]
            
            # 尋找數字 (包含逗號的數字，例如 10,000)
            # 移除非數字與逗號/點號以外的字元來萃取
            nums_str = re.findall(r'\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b|\b\d+\b', line_clean)
            
            # 轉換為 float (保留原始出現順序)
            parsed_nums = []
            for n_str in nums_str:
                try:
                    if '.' in n_str and ',' not in n_str:
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
                shares = 0
                price = 0
                
                # 策略 1: 尋找 a * b = c 的數學關係
                # 在越南股市，通常 a 是股數 (>=10)，b 是價格 (>=1000)，c 是總價
                for i in range(len(parsed_nums)):
                    for j in range(i+1, len(parsed_nums)):
                        a = parsed_nums[i]
                        b = parsed_nums[j]
                        min_val = min(a, b)
                        max_val = max(a, b)
                        if min_val >= 10 and max_val >= 1000:
                            product = a * b
                            # 檢查 product 是否在提取出的數字中
                            if any(abs(product - c) < 2 for c in parsed_nums):
                                shares = min_val
                                price = max_val
                                break
                    if shares > 0:
                        break
                        
                # 策略 2: 如果找不到相乘關係，利用出現順序的啟發式法則
                if shares == 0 or price == 0:
                    # 過濾掉極小的數字 (如 1, 2, 5 是日期或序號)，以及常見的年份 (如 2026)
                    large_nums = [n for n in parsed_nums if n >= 10 and n != 2024 and n != 2025 and n != 2026]
                    if len(large_nums) >= 2:
                        shares = min(large_nums[0], large_nums[1])
                        price = max(large_nums[0], large_nums[1])
                        
                # 防呆: 如果還是抓錯，例如價格小於 1000，可能是錯的
                if price < 1000 and shares >= 1000:
                    shares, price = price, shares
                    
                if shares > 0 and price > 0:
                    transactions.append({
                        "date": date_str,
                        "symbol": symbol,
                        "action": action,
                        "shares": shares,
                        "price": price,
                        "fee": 0 
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

def run_email_sync(user_id, start_date=None):
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
        
    try:
        mail.select("inbox")
        
        domains_to_search = []
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
        
        from datetime import datetime
        if start_date is None:
            start_date = datetime.now()
        since_imap = start_date.strftime("%d-%b-%Y")
        
        all_mail_ids = set()
        for domain in domains_to_search:
            # 改為搜尋「選定日期」的所有信件，不管是否已讀
            status, messages = mail.search(None, f'(SINCE "{since_imap}" FROM "{domain}")')
            if status == "OK":
                ids = messages[0].split()
                all_mail_ids.update(ids)
                
        mail_ids = list(all_mail_ids)
        found = len(mail_ids)
        inserted = 0
        debug_text = "" 
        
        for mid in mail_ids:
            res, msg_data = mail.fetch(mid, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # 解碼並檢查標題，如果包含投資日報等行銷關鍵字，直接略過以加速讀取
                    from email.header import decode_header
                    subject = msg.get("Subject", "")
                    decoded_subject = ""
                    for part, encoding in decode_header(subject):
                        if isinstance(part, bytes):
                            decoded_subject += part.decode(encoding or "utf-8", errors="ignore")
                        else:
                            decoded_subject += str(part)
                    
                    if any(kw in decoded_subject.upper() for kw in ["投資日報", "BẢN TIN", "NEWSLETTER"]):
                        continue
    
                    date_tuple = email.utils.parsedate_tz(msg['Date'])
                    if date_tuple:
                        local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                        date_str = local_date.strftime("%Y-%m-%d")
                    else:
                        date_str = datetime.now().strftime("%Y-%m-%d")
                    
                    text = extract_text_from_email(msg)
                    if not text.strip():
                        continue
                    debug_text = text # 記錄最後一封信的文字內容
                    txns = parse_broker_email(text, date_str, broker)
                    
                    # 為了避免重複匯入，先取得今日已有的交易紀錄
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
                            print(f"Error inserting {t}: {e}")
                            
            # 標記為已讀 (SEEN)
            # 測試階段可以先不標記，方便重複測試。但上線需要。
            mail.store(mid, '+FLAGS', '\\Seen')
                            
    finally:
        try:
            if mail.state == 'SELECTED':
                mail.close()
        except:
            pass
        try:
            mail.logout()
        except:
            pass
            
    return {"found": found, "inserted": inserted, "debug_text": debug_text}

if __name__ == "__main__":
    import sys
    if "--run-all-users" in sys.argv:
        print("Starting batch email sync for all users...")
        from supabase_db import _table
        # Get all users with IMAP settings
        try:
            res = _table("notification_settings").select("user_id").eq("key", "imap_email").execute()
            user_ids = list(set([r["user_id"] for r in (res.data or [])]))
            print(f"Found {len(user_ids)} users with IMAP configured.")
            
            for uid in user_ids:
                try:
                    print(f"Syncing for user {uid}...")
                    result = run_email_sync(uid)
                    print(f"User {uid}: Found {result['found']} emails, Inserted {result['inserted']} txns.")
                except Exception as e:
                    print(f"User {uid} failed: {e}")
        except Exception as e:
            print(f"Error fetching users: {e}")
    else:
        print("Run with --run-all-users to sync all accounts.")

