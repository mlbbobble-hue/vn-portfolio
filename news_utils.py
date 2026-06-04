import urllib.parse
import requests
import feedparser
import streamlit as st
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor, as_completed

def _fetch_and_translate_single(symbol, lang="zh", limit=2):
    try:
        news_list = []
        translator = GoogleTranslator(source='auto', target='zh-TW') if lang == "zh" else None
        
        # Restrict to reputable Vietnamese financial news sites
        trusted_sites = ["cafef.vn", "vietstock.vn", "vneconomy.vn", "tinnhanhchungkhoan.vn"]
        site_query = " OR ".join([f"site:{site}" for site in trusted_sites])
        
        # Query Google News for the stock symbol in Vietnam, limited to the past 24 hours
        query = urllib.parse.quote(f"{symbol} chứng khoán ({site_query}) when:1d")
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
                # Only translate if language is zh
                title_final = translator.translate(title) if lang == "zh" else title
                news_list.append({
                    "symbol": symbol,
                    "title": title_final,
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_news(symbol, lang="zh", limit=2):
    return _fetch_and_translate_single(symbol, lang, limit)

@st.cache_data(ttl=3600)
def fetch_all_news_parallel(symbols, lang="zh", limit=2):
    """
    Fetches and optionally translates news for multiple symbols in parallel.
    """
    all_news = []
    with ThreadPoolExecutor(max_workers=min(10, len(symbols))) as executor:
        future_to_symbol = {executor.submit(_fetch_and_translate_single, sym, lang, limit): sym for sym in symbols}
        
        for future in as_completed(future_to_symbol):
            try:
                result = future.result()
                if result:
                    all_news.extend(result)
            except Exception as e:
                sym = future_to_symbol[future]
                print(f"Parallel fetch failed for {sym}: {e}")
                
    return all_news
