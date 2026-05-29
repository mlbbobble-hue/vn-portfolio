"""
market_data.py — 市場數據抓取模組 (Migrated to vnstock.api v4)
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

# ── Monkey patch requests timeout so vnstock doesn't hang forever ──
original_request = requests.Session.request
def custom_request(self, method, url, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 3
    return original_request(self, method, url, **kwargs)
requests.Session.request = custom_request

def get_stock_price(symbol: str) -> dict:
    """
    取得單一股票即時（延遲）股價
    使用 vnstock.api.quote.Quote，支援多個 source 切換以防止 IP Block
    """
    symbol = symbol.upper().strip()
    sources = ['vci', 'kbs', 'msn', 'fmp']
    
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
                return {"symbol": symbol, "price": price, "change_pct": change_pct, "volume": volume}
        except Exception as e:
            logger.debug(f"vnstock Quote ({src}) failed for {symbol}: {e}")

    return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0}


import concurrent.futures

def get_multiple_prices(symbols: list[str], delay: float = 0.1) -> pd.DataFrame:
    results = []
    def fetch(sym):
        data = get_stock_price(sym)
        data["updated_at"] = datetime.now().strftime("%H:%M:%S")
        return data
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch, symbols))
        
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
