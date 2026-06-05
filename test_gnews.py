import requests
import feedparser
import urllib.parse
query = urllib.parse.quote("CII chứng khoán")
url = f"https://news.google.com/rss/search?q={query}&hl=vi&gl=VN&ceid=VN:vi"
res = requests.get(url)
print("Status:", res.status_code)
feed = feedparser.parse(res.text)
print("Found entries:", len(feed.entries))
if feed.entries:
    print(feed.entries[0].title)
