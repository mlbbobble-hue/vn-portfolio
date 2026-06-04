import urllib.parse
import requests
import feedparser
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_news(symbol, limit=3):
    """
    Fetches news for a given stock symbol using Google News RSS,
    without translation.
    """
    try:
        news_list = []
        # Query Google News for the stock symbol in Vietnam, limited to the past 24 hours
        query = urllib.parse.quote(f"{symbol} chứng khoán when:1d")
        url = f"https://news.google.com/rss/search?q={query}&hl=vi&gl=VN&ceid=VN:vi"
        
        res = requests.get(url, timeout=10)
        feed = feedparser.parse(res.text)
        
        if not feed.entries:
            return []
            
        for item in feed.entries[:limit]:
            title = getattr(item, 'title', '')
            link = getattr(item, 'link', '')
            pub_date = getattr(item, 'published', '')
            
            if not title:
                continue
                
            news_list.append({
                "symbol": symbol,
                "title": title,
                "link": link,
                "pubDate": pub_date
            })
                
        return news_list
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []
