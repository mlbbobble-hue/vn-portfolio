"""
market_data.py — 市場數據抓取模組 (Migrated to vnstock.api v4)
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

# ── Monkey patch requests timeout so vnstock doesn't hang forever ──
original_request = requests.Session.request
def custom_request(self, method, url, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 1.5  # 從 3 秒降到 1.5 秒，讓失敗的 source 更快放棄
    return original_request(self, method, url, **kwargs)
requests.Session.request = custom_request

# 記住每個 symbol 上次成功的 source，下次優先使用
_source_cache = {}

def get_stock_price(symbol: str) -> dict:
    """
    取得單一股票即時（延遲）股價
    使用 vnstock.api.quote.Quote，支援多個 source 切換以防止 IP Block
    """
    symbol = symbol.upper().strip()
    
    # 跳過明顯無效的代碼（例如帶有特殊後綴的）
    if len(symbol) > 10 or any(c in symbol for c in ['/', '\\', ' ']):
        return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0}

    # 把上次成功的 source 排到最前面
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
                _source_cache[symbol] = src  # 記住成功的 source
                return {"symbol": symbol, "price": price, "change_pct": change_pct, "volume": volume}
        except Exception as e:
            logger.debug(f"vnstock Quote ({src}) failed for {symbol}: {e}")

    return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0}


def get_multiple_prices(symbols: list[str], delay: float = 0.1, progress_callback=None) -> pd.DataFrame:
    """抓取多檔股價，使用 10 條平行執行緒加速"""
    results = []
    completed = 0
    total = len(symbols)
    
    def fetch(sym):
        data = get_stock_price(sym)
        data["updated_at"] = datetime.now().strftime("%H:%M:%S")
        return data
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch, sym) for sym in symbols]
        try:
            for future in concurrent.futures.as_completed(futures, timeout=20):
                try:
                    results.append(future.result())
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)
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
                    ex_date = row_dict.get("exright_date", "")
                    pay_date = row_dict.get("payout_date", "")
                    cash = float(row_dict.get("value_per_share", 0) or 0)
                    ratio = float(row_dict.get("exercise_ratio", 0) or 0)
                    if cash > 0 or ratio > 0:
                        div_type = "STOCK" if (ratio > 0 and cash == 0) else "CASH"
                        results.append({
                            "symbol": symbol,
                            "ex_date": str(ex_date)[:10] if pd.notnull(ex_date) else "",
                            "pay_date": str(pay_date)[:10] if pd.notnull(pay_date) else "",
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
