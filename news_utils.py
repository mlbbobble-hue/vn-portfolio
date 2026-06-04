import urllib.parse
import requests
import feedparser
from deep_translator import GoogleTranslator
import streamlit as st
from datetime import datetime
import time

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_and_translate_news(symbol, limit=2):
    """
    Fetches news for a given stock symbol using Google News RSS,
    and translates titles and summaries to Traditional Chinese.
    """
    try:
        translated_news = []
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
            
            # Google news titles often have " - SourceName" at the end, let's keep it clean
            if not title:
                continue
                
            try:
                # Translate
                title_zh = translator.translate(title)
                
                translated_news.append({
                    "symbol": symbol,
                    "title": title_zh,
                    "link": link,
                    "pubDate": pub_date,
                    "original_title": title
                })
            except Exception as e:
                # Fallback to original if translation fails
                translated_news.append({
                    "symbol": symbol,
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "original_title": title
                })
                
        return translated_news
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []
