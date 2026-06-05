import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """def extract_text_from_email(msg):
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
    return text"""

new_code = """import io
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
                    text += part.get_payload(decode=True).decode('utf-8', errors='ignore') + "\\n"
                except:
                    pass
            elif ctype == 'text/html' and 'attachment' not in cdispo:
                try:
                    from bs4 import BeautifulSoup
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    text += BeautifulSoup(html, "html.parser").get_text(separator=' ') + "\\n"
                except:
                    try:
                        text += part.get_payload(decode=True).decode('utf-8', errors='ignore') + "\\n"
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
                                    text += page_text + "\\n"
                    except Exception as e:
                        print(f"Error parsing PDF attachment: {e}")
    else:
        try:
            text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    return text"""

if target in content:
    content = content.replace(target, new_code)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py for PDF support")
else:
    print("Target not found in email_parser.py")
