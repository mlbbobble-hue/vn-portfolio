import urllib.parse
import requests
import feedparser
import streamlit as st
from deep_translator import GoogleTranslator

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_news(symbol, limit=3):
    """
    Fetches news for a given stock symbol using Google News RSS,
    and translates titles to Traditional Chinese.
    """
    try:
        news_list = []
        translator = GoogleTranslator(source='auto', target='zh-TW')
        
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
                
            try:
                # Translate title
                title_zh = translator.translate(title)
                news_list.append({
                    "symbol": symbol,
                    "title": title_zh,
                    "link": link,
                    "pubDate": pub_date,
                    "original_title": title
                })
            except Exception as e:
                # Fallback to original if translation fails
                news_list.append({
                    "symbol": symbol,
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "original_title": title
                })
                
        return news_list
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []
