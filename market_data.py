"""
market_data.py — 市場數據抓取模組
策略：優先使用 Google Finance 批次抓取（1 秒抓全部），失敗才 fallback 到 vnstock
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import logging
import concurrent.futures
import re
import json

logger = logging.getLogger(__name__)

# ── Monkey patch requests timeout so vnstock doesn't hang forever ──
original_request = requests.Session.request
def custom_request(self, method, url, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 2
    return original_request(self, method, url, **kwargs)
requests.Session.request = custom_request


# ══════════════════════════════════════════════════════════════
#  方法 1：直接讀取您的 Google Sheet（跟 GOOGLEFINANCE 一樣即時！）
#  一次 HTTP 請求就能拿到所有股票的最新報價，約 1~2 秒完成
# ══════════════════════════════════════════════════════════════

GOOGLE_SHEET_ID = "12Nk40-1E3knLX3nCkW8pxwBJWe3r-ITXfNncddas3WM"
GOOGLE_SHEET_GID = "1865847466"

_sheet_price_cache = {}  # symbol -> {price, change_pct}
_sheet_cache_time = None

def _refresh_sheet_cache():
    """從 Google Sheet 批次抓取所有股票報價（一次 HTTP 搞定）"""
    global _sheet_price_cache, _sheet_cache_time
    import csv, io
    
    try:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid={GOOGLE_SHEET_GID}"
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            logger.debug(f"Google Sheet fetch failed: HTTP {resp.status_code}")
            return False
        
        reader = csv.reader(io.StringIO(resp.text))
        header = next(reader)  # Skip header row
        
        new_cache = {}
        for row in reader:
            if len(row) >= 4 and row[0] and row[3]:
                sym = row[0].replace(".VN", "").strip().upper()
                try:
                    price_str = row[3].replace(",", "")
                    price = float(price_str)
                    if price > 0:
                        new_cache[sym] = {"price": price, "change_pct": 0, "volume": 0}
                except (ValueError, IndexError):
                    continue
        
        if new_cache:
            _sheet_price_cache = new_cache
            _sheet_cache_time = datetime.now()
            logger.info(f"Google Sheet cache refreshed: {len(new_cache)} symbols")
            return True
    except Exception as e:
        logger.debug(f"Google Sheet fetch error: {e}")
    return False


def _fetch_from_sheet(symbol: str) -> dict | None:
    """從 Google Sheet 快取中取得報價"""
    sym = symbol.upper().strip()
    cached = _sheet_price_cache.get(sym)
    if cached:
        return {"symbol": sym, "price": cached["price"], "change_pct": cached["change_pct"], "volume": cached.get("volume", 0)}
    return None


# ══════════════════════════════════════════════════════════════
#  方法 2：vnstock fallback（較慢但穩定）
# ══════════════════════════════════════════════════════════════

# 記住每個 symbol 上次成功的 source，下次優先使用
_source_cache = {}

def _fetch_vnstock(symbol: str) -> dict:
    """使用 vnstock API 抓取股價（fallback 用）"""
    symbol = symbol.upper().strip()
    
    if len(symbol) > 10 or any(c in symbol for c in ['/', '\\', ' ']):
        return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0}

    all_sources = ['vci', 'kbs', 'msn', 'fmp']
    last_good = _source_cache.get(symbol)
    if last_good and last_good in all_sources:
        sources = [last_good] + [s for s in all_sources if s != last_good]
    else:
        sources = all_sources
    
    for src in sources:
        try:
            from vnstock.api.quote import Quote
            q = Quote(symbol=symbol, source=src, show_log=False)
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
            df = q.history(start=yesterday, end=today, interval='1D')
            if df is not None and not df.empty:
                row = df.iloc[-1]
                prev = df.iloc[-2] if len(df) >= 2 else row
                
                price = float(row.get('close', 0)) * 1000
                prev_price = float(prev.get('close', price)) * 1000
                change_pct = ((price - prev_price) / prev_price * 100) if prev_price else 0
                volume = float(row.get('volume', 0))
                _source_cache[symbol] = src
                return {"symbol": symbol, "price": price, "change_pct": change_pct, "volume": volume}
        except Exception as e:
            logger.debug(f"vnstock Quote ({src}) failed for {symbol}: {e}")

    return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0}


# ══════════════════════════════════════════════════════════════
#  公開 API
# ══════════════════════════════════════════════════════════════

def get_stock_price(symbol: str) -> dict:
    """取得單一股票報價：先查 Sheet 快取，沒有才用 vnstock"""
    result = _fetch_from_sheet(symbol)
    if result and result["price"] > 0:
        return result
    return _fetch_vnstock(symbol)


def get_multiple_prices(symbols: list[str], delay: float = 0.1, progress_callback=None) -> pd.DataFrame:
    """
    批次抓取多檔股價。
    策略：
    1. 先用一次 HTTP 從 Google Sheet 批次拿到所有報價（~2 秒）
    2. 沒拿到的才用 vnstock fallback（平行 10 執行緒）
    """
    results = []
    total = len(symbols)
    
    # Step 1: 從 Google Sheet 一次拿全部
    _refresh_sheet_cache()
    
    missing_symbols = []
    for sym in symbols:
        sheet_result = _fetch_from_sheet(sym)
        if sheet_result and sheet_result["price"] > 0:
            sheet_result["updated_at"] = datetime.now().strftime("%H:%M:%S")
            results.append(sheet_result)
        else:
            missing_symbols.append(sym)
    
    if progress_callback:
        progress_callback(len(results), total)
    
    # Step 2: 沒拿到的用 vnstock fallback
    if missing_symbols:
        def fetch_fallback(sym):
            data = _fetch_vnstock(sym)
            data["updated_at"] = datetime.now().strftime("%H:%M:%S")
            return data
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_fallback, sym) for sym in missing_symbols]
            try:
                for future in concurrent.futures.as_completed(futures, timeout=15):
                    try:
                        results.append(future.result())
                        if progress_callback:
                            progress_callback(len(results), total)
                    except Exception:
                        pass
            except concurrent.futures.TimeoutError:
                pass
        
    return pd.DataFrame(results)


def get_dividend_history(symbol: str) -> list[dict]:
    symbol = symbol.upper().strip()
    results = []
    sources = ['vci', 'kbs', 'msn']
    
    for src in sources:
        try:
            from vnstock.api.company import Company
            c = Company(symbol=symbol, source=src, show_log=False)
            df = c.events()
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    row_dict = dict(row)
                    ex_date = row_dict.get("exright_date", None)
                    pay_date = row_dict.get("payout_date", None)
                    rec_date = row_dict.get("record_date", None)
                    
                    if pd.isna(ex_date) or str(ex_date).strip() == "" or str(ex_date) == "NaT":
                        continue

                    cash = row_dict.get("value_per_share", 0)
                    if pd.isna(cash): cash = 0
                    cash = float(cash)
                    
                    ratio = row_dict.get("exercise_ratio", 0)
                    if pd.isna(ratio): ratio = 0
                    ratio = float(ratio)

                    if cash > 0 or ratio > 0:
                        div_type = "STOCK" if (ratio > 0 and cash == 0) else "CASH"
                        results.append({
                            "symbol": symbol,
                            "ex_date": str(ex_date)[:10],
                            "record_date": str(rec_date)[:10] if pd.notnull(rec_date) and str(rec_date).strip() != "" and str(rec_date) != "NaT" else None,
                            "pay_date": str(pay_date)[:10] if pd.notnull(pay_date) and str(pay_date).strip() != "" and str(pay_date) != "NaT" else None,
                            "type": div_type,
                            "cash_amount": cash,
                            "stock_ratio": ratio,
                        })
                return results # 若成功抓到，直接回傳
        except Exception as e:
            logger.debug(f"vnstock Company ({src}) failed for {symbol}: {e}")
            
    return results


def get_moving_average(symbol: str, period: int = 60) -> float | None:
    sources = ['vci', 'kbs', 'msn']
    for src in sources:
        try:
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=period * 2)).strftime("%Y-%m-%d")
            from vnstock.api.quote import Quote
            q = Quote(symbol=symbol, source=src, show_log=False)
            df = q.history(start=start, end=end, interval='1D')
            if df is None or df.empty: continue
            prices = df['close'].dropna()
            if len(prices) >= period:
                return float(prices.tail(period).mean()) * 1000
        except Exception:
            pass
    return None


def get_historical_prices(symbol: str, days: int = 365) -> pd.DataFrame:
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    sources = ['vci', 'kbs', 'msn']
    for src in sources:
        try:
            from vnstock.api.quote import Quote
            q = Quote(symbol=symbol, source=src, show_log=False)
            df = q.history(start=start, end=end, interval='1D')
            if df is not None and not df.empty:
                df['close'] = df['close'].astype(float) * 1000
                return df
        except Exception:
            pass
    return pd.DataFrame()
