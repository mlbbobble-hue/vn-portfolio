import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    txns = []
    
    # 簡易特徵萃取 (針對各家券商的成交回報格式)
    if broker in ["TCBS", "SSI", "VNDIRECT", "PHS", "ALL (搜尋全部券商)"]:
        # 這裡示範一種通用型的正則表達式擷取邏輯，實際情況需根據各券商信件微調
        for line in text.split('\\n'):
            line_clean = line.strip().upper()
            is_buy = "MUA" in line_clean or "BUY" in line_clean
            is_sell = "BÁN" in line_clean or "BAN" in line_clean or "SELL" in line_clean
            
            if is_buy or is_sell:
                symbols = re.findall(r'\\b[A-Z]{3}\\b', line_clean)
                numbers = re.findall(r'\\b\\d+(?:,\\d+)*(?:\\.\\d+)?\\b', line_clean)
                
                if symbols and len(numbers) >= 2:"""

new_code = """    txns = []
    
    # 忽略市場報告/日報，避免誤判
    if "投資日報" in text or "Bản tin" in text or "Newsletter" in text:
        return txns
    
    # 簡易特徵萃取 (針對各家券商的成交回報格式)
    if broker in ["TCBS", "SSI", "VNDIRECT", "PHS", "ALL (搜尋全部券商)"]:
        # 這裡示範一種通用型的正則表達式擷取邏輯，實際情況需根據各券商信件微調
        for line in text.split('\\n'):
            line_clean = line.strip().upper()
            
            # 必須是獨立的單字，不能是 THU BAN WARD 這種包含關係
            is_buy = bool(re.search(r'\\b(MUA|BUY)\\b', line_clean))
            is_sell = bool(re.search(r'\\b(BÁN|BAN|SELL)\\b', line_clean))
            
            # 必須包含成交或價格相關的關鍵字才當作是交易明細行 (避免讀到地址)
            has_txn_keywords = bool(re.search(r'(GIÁ|PRICE|KHỚP|MATCH|LỆNH|ORDER|VND|ĐỒNG)', line_clean))
            
            if (is_buy or is_sell) and has_txn_keywords:
                symbols = re.findall(r'\\b[A-Z]{3}\\b', line_clean)
                # 過濾掉常見的非股票代號3字母
                ignore_list = {"VND", "USD", "THU", "BAN", "HAI", "HON", "DAO", "VAN", "WAR", "HCM", "HNX", "OTC", "UPC", "MUA", "BUY", "GIA", "PHI"}
                symbols = [s for s in symbols if s not in ignore_list]
                
                numbers = re.findall(r'\\b\\d+(?:,\\d+)*(?:\\.\\d+)?\\b', line_clean)
                
                if symbols and len(numbers) >= 2:"""

if target in content:
    content = content.replace(target, new_code)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py to use strict parsing logic")
else:
    print("Target not found in email_parser.py")
