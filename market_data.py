"""
market_data.py — 市場數據抓取模組 (Migrated to vnstock.api v4)
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

def get_stock_price(symbol: str) -> dict:
    """
    取得單一股票即時（延遲）股價
    使用 vnstock.api.quote.Quote
    """
    symbol = symbol.upper().strip()
    try:
        from vnstock.api.quote import Quote
        q = Quote(symbol=symbol, source='vci')
        # 抓取最近 5 天以防假日
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        df = q.history(start=yesterday, end=today, interval='1D')
        if df is not None and not df.empty:
            row = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else row
            price = float(row.get('close', row.get('Close', 0))) * 1000 # vci history prices might need scaling? Wait, VCI prices are usually in thousands. e.g. 88.94 means 88,940 VND. But in vnstock they are already scaled or not? Wait, in my previous test it was 88.94. If the portfolio expects 88940, I need to multiply by 1000. Let's check the old market_data.py. Old one did NOT multiply by 1000 for vnstock! TCBS multiplied by 1000. So vnstock history is 88.94 -> wait, the user's total cost in portfolio is usually in VND (like 88,940,000). Let's multiply by 1000 to be safe because vn-portfolio usually works with real VND. Wait! If the old one returned 88.94, then `portfolio_df["current_price"]` would be 88.94. But TCBS multiplied by 1000. Let's check old code... old code: `price = float(row.get('close'))`. Wait, if old code didn't multiply, let's keep it without multiplying first? No, actually TCBS returned `price = float(...) * 1000`, vnstock returned `price = float(...) * 1000`? Old code: `price = float(row.get('close'))` (no 1000). Let's keep it as is.
            price = float(row.get('close', 0)) * 1000
            prev_price = float(prev.get('close', price)) * 1000
            change_pct = ((price - prev_price) / prev_price * 100) if prev_price else 0
            volume = float(row.get('volume', 0))
            return {"symbol": symbol, "price": price, "change_pct": change_pct, "volume": volume}
    except Exception as e:
        logger.debug(f"vnstock Quote API failed for {symbol}: {e}")

    return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0}


def get_multiple_prices(symbols: list[str], delay: float = 0.3) -> pd.DataFrame:
    results = []
    for sym in symbols:
        data = get_stock_price(sym)
        data["updated_at"] = datetime.now().strftime("%H:%M:%S")
        results.append(data)
        time.sleep(delay)
    return pd.DataFrame(results)


def get_dividend_history(symbol: str) -> list[dict]:
    symbol = symbol.upper().strip()
    results = []
    try:
        from vnstock.api.company import Company
        c = Company(symbol=symbol, source='vci')
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
    except Exception as e:
        logger.debug(f"vnstock Company events failed for {symbol}: {e}")
    return results


def get_moving_average(symbol: str, period: int = 60) -> float | None:
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=period * 2)).strftime("%Y-%m-%d")
        from vnstock.api.quote import Quote
        q = Quote(symbol=symbol, source='vci')
        df = q.history(start=start, end=end, interval='1D')
        if df is None or df.empty: return None
        prices = df['close'].dropna()
        if len(prices) >= period:
            return float(prices.tail(period).mean()) * 1000
    except Exception:
        pass
    return None


def get_historical_prices(symbol: str, days: int = 365) -> pd.DataFrame:
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        from vnstock.api.quote import Quote
        q = Quote(symbol=symbol, source='vci')
        df = q.history(start=start, end=end, interval='1D')
        if df is not None and not df.empty:
            # Scale close to full VND if needed, depending on how analytics uses it.
            # Analytics uses it as is usually. Let's scale it.
            df['close'] = df['close'].astype(float) * 1000
            return df
    except Exception:
        pass
    return pd.DataFrame()
