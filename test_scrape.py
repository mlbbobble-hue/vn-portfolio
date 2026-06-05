import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

url = "https://finance.vietstock.vn/FPT/tin-tuc-su-kien.htm"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

news_list = []
# Try to find news items
articles = soup.find_all("div", class_="single_news")
print(f"Found {len(articles)} articles with class 'single_news'")

# Sometimes it's inside a different class
if not articles:
    articles = soup.find_all("article")
    print(f"Found {len(articles)} articles with tag 'article'")

if not articles:
    articles = soup.select("h3 a")
    print(f"Found {len(articles)} articles with selector 'h3 a'")

for a in articles[:3]:
    if a.name == 'a':
        title = a.text.strip()
        link = a.get("href")
    else:
        a_tag = a.find("a")
        title = a_tag.text.strip() if a_tag else "No title"
        link = a_tag.get("href") if a_tag else ""
    
    print(f"Title (VI): {title}")
    
    # Translate to Chinese
    try:
        translated = GoogleTranslator(source='auto', target='zh-TW').translate(title)
        print(f"Title (ZH): {translated}")
    except Exception as e:
        print(f"Translation error: {e}")
    print("---")
