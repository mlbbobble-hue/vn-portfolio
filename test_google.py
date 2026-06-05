import requests
from bs4 import BeautifulSoup
url = "https://news.google.com/search?q=cổ%20phiếu%20FPT%20vietstock&hl=vi&gl=VN&ceid=VN%3Avi"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
try:
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.find_all("article")
    print(f"Found {len(articles)} articles")
    for a in articles[:3]:
        link = a.find("a")
        if link: print(link.text)
except Exception as e:
    print(e)
