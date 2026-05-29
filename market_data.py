"""
市場數據抓取模組 — 整合 vnstock 套件，並提供 fallback 機制
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

# ── vnstock 動態載入（相容新舊版本）────────────────────────────

def _get_vnstock_price(symbol: str) -> dict | None:
    """嘗試用 vnstock 取得即時股價，相容 v3 與 v4 API"""
    try:
        # 嘗試 v4 / Unified API
        from vnstock import Vnstock
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        df = stock.quote.history(start=yesterday, end=today, interval='1D')
        if df is not None and not df.empty:
            row = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else row
            price = float(row.get('close', row.get('Close', 0)))
            prev_price = float(prev.get('close', prev.get('Close', price)))
            change_pct = ((price - prev_price) / prev_price * 100) if prev_price else 0
            volume = float(row.get('volume', row.get('Volume', 0)))
            return {"symbol": symbol, "price": price, "change_pct": change_pct, "volume": volume}
    except Exception as e:
        logger.debug(f"vnstock v4 failed for {symbol}: {e}")

    try:
        # 嘗試 v3 API
        from vnstock import stock_historical_data
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        df = stock_historical_data(symbol=symbol, start_date=yesterday, end_date=today,
                                   resolution='1D', type='stock')
        if df is not None and not df.empty:
            price = float(df.iloc[-1]['close'])
            prev = float(df.iloc[-2]['close']) if len(df) >= 2 else price
            change_pct = ((price - prev) / prev * 100) if prev else 0
            volume = float(df.iloc[-1].get('volume', 0))
            return {"symbol": symbol, "price": price, "change_pct": change_pct, "volume": volume}
    except Exception as e:
        logger.debug(f"vnstock v3 failed for {symbol}: {e}")

    return None


def _get_tcbs_price(symbol: str) -> dict | None:
    """TCBS 公開 API 備用方案"""
    try:
        url = f"https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term"
        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=7)).timestamp())
        params = {"ticker": symbol, "type": "stock", "resolution": "D",
                  "from": start, "to": end}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        r = requests.get(url, params=params, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            bars = data.get("data", [])
            if bars and len(bars) >= 1:
                latest = bars[-1]
                price = float(latest.get("close", 0)) * 1000  # TCBS 回傳的是千分之一
                prev_price = float(bars[-2].get("close", latest["close"])) * 1000 if len(bars) >= 2 else price
                change_pct = ((price - prev_price) / prev_price * 100) if prev_price else 0
                volume = float(latest.get("volume", 0))
                return {"symbol": symbol, "price": price, "change_pct": change_pct, "volume": volume}
    except Exception as e:
        logger.debug(f"TCBS API failed for {symbol}: {e}")
    return None


def _get_ssi_price(symbol: str) -> dict | None:
    """SSI 公開 API 備用方案"""
    try:
        url = "https://fc-data.ssi.com.vn/api/v2/Market/Securities"
        params = {"market": "HOSE", "PageIndex": 1, "PageSize": 10,
                  "lookupRequest": symbol}
        headers = {"Accept": "application/json"}
        r = requests.get(url, params=params, headers=headers, timeout=8)
        if r.status_code == 200:
            items = r.json().get("data", {}).get("list", [])
            for item in items:
                if item.get("Symbol", "").upper() == symbol.upper():
                    price = float(item.get("LastPrice", 0)) * 1000
                    ref   = float(item.get("RefPrice", price)) * 1000
                    change_pct = ((price - ref) / ref * 100) if ref else 0
                    volume = float(item.get("TotalVol", 0))
                    return {"symbol": symbol, "price": price,
                            "change_pct": change_pct, "volume": volume}
    except Exception as e:
        logger.debug(f"SSI API failed for {symbol}: {e}")
    return None


def get_stock_price(symbol: str) -> dict:
    """
    取得單一股票即時（延遲）股價
    依序嘗試：vnstock → TCBS API → SSI API → 回傳 None
    """
    symbol = symbol.upper().strip()
    for fn in [_get_vnstock_price, _get_tcbs_price, _get_ssi_price]:
        result = fn(symbol)
        if result and result.get("price", 0) > 0:
            return result
    logger.warning(f"無法取得 {symbol} 的股價")
    return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0}


def get_multiple_prices(symbols: list[str], delay: float = 0.3) -> pd.DataFrame:
    """
    批次取得多個股票股價，回傳 DataFrame
    每次請求之間加入延遲，避免觸發 API 速率限制
    """
    results = []
    for sym in symbols:
        data = get_stock_price(sym)
        data["updated_at"] = datetime.now().strftime("%H:%M:%S")
        results.append(data)
        time.sleep(delay)
    return pd.DataFrame(results)


# ══════════════════════════════════════════════════════════════
#  配息歷史數據
# ══════════════════════════════════════════════════════════════

def get_dividend_history(symbol: str) -> list[dict]:
    """取得股票配息歷史，回傳標準化的 dict list"""
    symbol = symbol.upper().strip()
    results = []

    # 方法一：vnstock v4
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        df = stock.company.dividends()
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                results.append(_normalize_dividend_row(symbol, row))
            if results:
                return results
    except Exception as e:
        logger.debug(f"vnstock v4 dividend failed for {symbol}: {e}")

    # 方法二：vnstock v3
    try:
        from vnstock import dividend_history
        df = dividend_history(symbol)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                results.append(_normalize_dividend_row(symbol, row))
            if results:
                return results
    except Exception as e:
        logger.debug(f"vnstock v3 dividend failed for {symbol}: {e}")

    return results


def _normalize_dividend_row(symbol: str, row) -> dict:
    """將不同來源的配息資料標準化"""
    row_dict = dict(row)
    
    # 嘗試從各種可能的欄位名稱取得值
    ex_date = (row_dict.get("exerciseDate") or row_dict.get("ex_date") or 
               row_dict.get("ExDate") or "")
    pay_date = (row_dict.get("issueDate") or row_dict.get("pay_date") or 
                row_dict.get("PayDate") or "")
    dtype = (row_dict.get("cashDividend") or row_dict.get("type") or "")
    cash = float(row_dict.get("cashDividend", 0) or row_dict.get("cash_amount", 0) or 0)
    ratio = float(row_dict.get("stockDividend", 0) or row_dict.get("stock_ratio", 0) or 0)

    # 判斷配息類型
    if ratio > 0 and cash == 0:
        div_type = "STOCK"
    else:
        div_type = "CASH"

    return {
        "symbol": symbol,
        "ex_date": str(ex_date)[:10] if ex_date else "",
        "pay_date": str(pay_date)[:10] if pay_date else "",
        "type": div_type,
        "cash_amount": cash,
        "stock_ratio": ratio,
    }


# ══════════════════════════════════════════════════════════════
#  MA 技術指標計算
# ══════════════════════════════════════════════════════════════

def get_moving_average(symbol: str, period: int = 60) -> float | None:
    """
    計算指定股票的移動平均線
    period: 天數（例如 60 = MA60）
    """
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=period * 2)).strftime("%Y-%m-%d")

        # 嘗試 vnstock v4
        try:
            from vnstock import Vnstock
            stock = Vnstock().stock(symbol=symbol, source='VCI')
            df = stock.quote.history(start=start, end=end, interval='1D')
        except Exception:
            from vnstock import stock_historical_data
            df = stock_historical_data(symbol=symbol, start_date=start, end_date=end,
                                       resolution='1D', type='stock')

        if df is None or df.empty:
            return None

        close_col = next((c for c in df.columns if c.lower() == 'close'), None)
        if close_col is None:
            return None

        prices = df[close_col].dropna()
        if len(prices) >= period:
            return float(prices.tail(period).mean())
    except Exception as e:
        logger.debug(f"MA{period} calculation failed for {symbol}: {e}")
    return None


def get_historical_prices(symbol: str, days: int = 365) -> pd.DataFrame:
    """取得歷史股價，用於圖表繪製"""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        df = stock.quote.history(start=start, end=end, interval='1D')
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    try:
        from vnstock import stock_historical_data
        df = stock_historical_data(symbol=symbol, start_date=start, end_date=end,
                                   resolution='1D', type='stock')
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    return pd.DataFrame()
