import yfinance as yf
from deep_translator import GoogleTranslator
import streamlit as st
import time

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_and_translate_news(symbol, limit=3):
    """
    Fetches news for a given stock symbol using yfinance
    and translates titles and summaries to Traditional Chinese.
    """
    try:
        # Add .VN for Vietnam stocks
        ticker_symbol = f"{symbol}.VN"
        ticker = yf.Ticker(ticker_symbol)
        raw_news = ticker.news
        
        if not raw_news:
            return []
            
        translated_news = []
        translator = GoogleTranslator(source='auto', target='zh-TW')
        
        for item in raw_news[:limit]:
            # yfinance news structure changed recently, content is often nested
            content = item.get('content', item)
            
            title = content.get('title', '')
            summary = content.get('summary', '')
            link = content.get('clickThroughUrl', {}).get('url', '') or content.get('link', '')
            pub_date = content.get('pubDate', '')
            
            if not title:
                continue
                
            try:
                # Translate
                title_zh = translator.translate(title)
                summary_zh = translator.translate(summary) if summary else ""
                
                translated_news.append({
                    "symbol": symbol,
                    "title": title_zh,
                    "summary": summary_zh,
                    "link": link,
                    "pubDate": pub_date,
                    "original_title": title
                })
            except Exception as e:
                # Fallback to original if translation fails
                translated_news.append({
                    "symbol": symbol,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "pubDate": pub_date,
                    "original_title": title
                })
                
        return translated_news
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []
