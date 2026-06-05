import requests
from bs4 import BeautifulSoup
url = "https://s.cafef.vn/tim-kiem.chn?keyword=CII"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}
res = requests.get(url, headers=headers)
print("Status:", res.status_code)
soup = BeautifulSoup(res.text, "html.parser")
news = soup.find_all("div", class_="news-item")
print(f"Found {len(news)} news items (class=news-item)")
for n in soup.find_all("a")[:10]:
    if "tin-tuc" in n.get("href", ""):
        print(n.text.strip())
        print(n.get("href"))
