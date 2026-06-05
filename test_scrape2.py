import requests
from bs4 import BeautifulSoup

url = "https://finance.vietstock.vn/FPT/tin-tuc-su-kien.htm"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

try:
    res = requests.get(url, headers=headers, timeout=10)
    print("Status:", res.status_code)
    soup = BeautifulSoup(res.text, "html.parser")
    news_titles = soup.select("h3, h4, h5, a")
    found = 0
    for el in news_titles:
        if "tin tức" in el.text.lower() or "news" in el.text.lower() or el.get("href", "").find("tin-tuc") != -1:
            if el.text.strip() and len(el.text.strip()) > 10:
                print(el.text.strip())
                found += 1
                if found > 5: break
except Exception as e:
    print(e)
