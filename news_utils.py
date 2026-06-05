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
            
        import email.utils
        from datetime import datetime, timezone, timedelta
        vn_tz = timezone(timedelta(hours=7))
        today_date = datetime.now(vn_tz).date()
            
        valid_count = 0
        for item in feed.entries:
            title = getattr(item, 'title', '')
            link = getattr(item, 'link', '')
            pub_date = getattr(item, 'published', '')
            
            if not title or not pub_date:
                continue
                
            # Strictly filter for TODAY's news only
            try:
                parsed_dt = email.utils.parsedate_to_datetime(pub_date)
                news_date = parsed_dt.astimezone(vn_tz).date()
                if news_date != today_date:
                    continue
            except Exception:
                continue # Skip if date cannot be parsed
                
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
            
            valid_count += 1
            if valid_count >= limit:
                break
                
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
