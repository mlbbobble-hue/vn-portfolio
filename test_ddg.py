import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_ddg(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for a in soup.find_all("a", class_="result__url", limit=3):
        results.append(a.get('href'))
    for title in soup.find_all("h2", class_="result__title", limit=3):
        print(title.text.strip())
    print("Links:", results)
search_ddg("cổ phiếu CII tin tức site:cafef.vn OR site:vietstock.vn")
