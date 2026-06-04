"""
持倉計算模組 — 加權平均成本法（WAC）
"""
import pandas as pd
from db_router import get_all_transactions, get_price_cache, get_dividend_events


def get_total_realized_pl() -> float:
    txns = get_all_transactions()
    if txns.empty: return 0.0
    
    txns = txns.sort_values(["date", "id"])
    holdings = {}
    total_realized = 0.0
    
    for _, row in txns.iterrows():
        sym = row["symbol"]
        action = row["action"]
        shares = float(row["shares"])
        price = float(row["price"])
        fee = float(row["fee"])
        
        if sym not in holdings:
            holdings[sym] = {"shares": 0.0, "avg_cost": 0.0, "total_cost": 0.0}
            
        h = holdings[sym]
        if action == "BUY":
            cost_of_new = shares * price + fee
            new_total_shares = h["shares"] + shares
            h["avg_cost"] = (h["total_cost"] + cost_of_new) / new_total_shares if new_total_shares > 0 else 0
            h["total_cost"] += cost_of_new
            h["shares"] = new_total_shares
        elif action == "SELL":
            sell_value = shares * price - fee
            cost_basis = shares * h["avg_cost"]
            total_realized += sell_value - cost_basis
            h["shares"] = max(0.0, h["shares"] - shares)
            h["total_cost"] = h["shares"] * h["avg_cost"]
            
    return total_realized


def compute_holdings() -> pd.DataFrame:
    """
    計算所有持股的庫存股數與平均持股成本（WAC）
    
    回傳 DataFrame 欄位：
      symbol, broker_breakdown, total_shares, avg_cost,
      total_cost, realized_pl
    """
    txns = get_all_transactions()
    if txns.empty:
        return pd.DataFrame(columns=[
            "symbol", "total_shares", "avg_cost", "total_cost",
            "realized_pl", "broker_breakdown"
        ])

    holdings = {}  # symbol -> {shares, avg_cost, total_cost, realized_pl}
    broker_map = {}  # symbol -> {broker -> shares}

    # 依時間排序
    txns = txns.sort_values(["date", "id"])

    for _, row in txns.iterrows():
        sym    = row["symbol"]
        action = row["action"]
        shares = float(row["shares"])
        price  = float(row["price"])
        fee    = float(row["fee"])
        broker = row["broker"]

        if sym not in holdings:
            holdings[sym] = {"shares": 0.0, "avg_cost": 0.0,
                             "total_cost": 0.0, "realized_pl": 0.0}
        if sym not in broker_map:
            broker_map[sym] = {}

        h = holdings[sym]

        if action == "BUY":
            cost_of_new = shares * price + fee
            new_total_shares = h["shares"] + shares
            h["avg_cost"] = (h["total_cost"] + cost_of_new) / new_total_shares if new_total_shares > 0 else 0
            h["total_cost"] += cost_of_new
            h["shares"] = new_total_shares
            broker_map[sym][broker] = broker_map[sym].get(broker, 0) + shares

        elif action == "SELL":
            sell_value = shares * price - fee
            cost_basis  = shares * h["avg_cost"]
            h["realized_pl"] += sell_value - cost_basis
            h["shares"] = max(0.0, h["shares"] - shares)
            h["total_cost"] = h["shares"] * h["avg_cost"]
            # 更新券商持股
            broker_map[sym][broker] = max(0, broker_map[sym].get(broker, 0) - shares)

    # 整理成 DataFrame，過濾掉已清倉（shares < 1）
    rows = []
    for sym, h in holdings.items():
        if h["shares"] < 1:
            continue
        rows.append({
            "symbol":           sym,
            "total_shares":     h["shares"],
            "avg_cost":         h["avg_cost"],
            "total_cost":       h["total_cost"],
            "realized_pl":      h["realized_pl"],
            "broker_breakdown": broker_map.get(sym, {}),
        })

    return pd.DataFrame(rows)


def apply_stock_dividend(symbol: str, stock_ratio: float) -> dict:
    """
    套用股票股利：自動調整庫存股數與平均成本
    stock_ratio: 例如 0.15 代表每 100 股配 15 股
    
    回傳：{"new_shares": ..., "new_avg_cost": ...}
    """
    holdings = compute_holdings()
    if holdings.empty:
        return {}
    row = holdings[holdings["symbol"] == symbol]
    if row.empty:
        return {}

    old_shares   = float(row.iloc[0]["total_shares"])
    old_avg_cost = float(row.iloc[0]["avg_cost"])

    new_shares   = old_shares * (1 + stock_ratio)
    new_avg_cost = old_avg_cost / (1 + stock_ratio)  # 成本不變，但每股成本下降

    return {
        "symbol":       symbol,
        "old_shares":   old_shares,
        "new_shares":   new_shares,
        "old_avg_cost": old_avg_cost,
        "new_avg_cost": new_avg_cost,
        "stock_ratio":  stock_ratio,
    }


def compute_portfolio_with_prices(holdings: pd.DataFrame = None,
                                  price_cache: pd.DataFrame = None) -> pd.DataFrame:
    """
    將持倉數據與即時股價合併，計算：
      - current_price：即時股價
      - market_value：即時市值
      - unrealized_pl：未實現損益
      - roi_pct：報酬率 %
      - change_pct：當日漲跌 %
    """
    if holdings is None:
        holdings = compute_holdings()
    if holdings.empty:
        return pd.DataFrame()

    if price_cache is None:
        price_cache = get_price_cache()

    if not price_cache.empty:
        price_map = price_cache.set_index("symbol")[["price", "change_pct"]].to_dict("index")
    else:
        price_map = {}

    rows = []
    for _, h in holdings.iterrows():
        sym    = h["symbol"]
        shares = h["total_shares"]
        avg_c  = h["avg_cost"]

        p_data     = price_map.get(sym, {})
        cur_price  = p_data.get("price", 0)
        change_pct = p_data.get("change_pct", 0)

        market_val    = cur_price * shares
        unrealized_pl = (cur_price - avg_c) * shares if cur_price > 0 else 0
        roi_pct       = ((cur_price - avg_c) / avg_c * 100) if avg_c > 0 and cur_price > 0 else 0

        rows.append({
            "symbol":         sym,
            "total_shares":   shares,
            "avg_cost":       avg_c,
            "current_price":  cur_price,
            "change_pct":     change_pct,
            "market_value":   market_val,
            "total_cost":     h["total_cost"],
            "unrealized_pl":  unrealized_pl,
            "realized_pl":    h["realized_pl"],
            "roi_pct":        roi_pct,
            "broker_breakdown": h.get("broker_breakdown", {}),
        })

    df = pd.DataFrame(rows)
    return df


def get_dividend_income_summary(holdings_symbols: list[str]) -> pd.DataFrame:
    """
    計算各股票預估年度現金股利收入
    基於過去的配息記錄推算
    """
    all_divs = get_dividend_events()
    if all_divs.empty:
        return pd.DataFrame()

    holdings = compute_holdings()
    if holdings.empty:
        return pd.DataFrame()

    shares_map = holdings.set_index("symbol")["total_shares"].to_dict()

    rows = []
    for sym in holdings_symbols:
        sym_divs = all_divs[
            (all_divs["symbol"] == sym) & (all_divs["type"] == "CASH")
        ]
        annual_cash = sym_divs["cash_amount"].sum()
        my_shares   = shares_map.get(sym, 0)
        est_income  = annual_cash * my_shares
        rows.append({
            "symbol":        sym,
            "annual_dps":    annual_cash,   # 每股年度現金股利
            "my_shares":     my_shares,
            "est_income":    est_income,    # 我的預估年收入
        })

    return pd.DataFrame(rows)


def get_estimated_yield(symbol: str, current_price: float, annual_dps: float) -> float:
    """計算預估殖利率"""
    if current_price <= 0:
        return 0.0
    return (annual_dps / current_price) * 100

def compute_received_dividends() -> tuple[float, dict, list]:
    """
    計算實際收到的歷史配息與配股。
    根據每次除權息日 (ex_date) 前的持股數來計算。
    回傳: (total_cash, stock_received_dict, detailed_history_list)
    """
    txns = get_all_transactions()
    divs = get_dividend_events()
    
    if txns.empty or divs.empty:
        return 0.0, {}, []

    txns["date_dt"] = pd.to_datetime(txns["date"], errors="coerce")
    txns = txns.dropna(subset=["date_dt"]).sort_values("date_dt")
    
    divs["ex_date_dt"] = pd.to_datetime(divs["ex_date"], errors="coerce")
    divs = divs.dropna(subset=["ex_date_dt"]).sort_values("ex_date_dt")
    
    total_cash = 0.0
    stock_received = {}
    details = []

    for _, div in divs.iterrows():
        sym = div["symbol"]
        ex_date = div["ex_date_dt"]
        
        # 必須在除息日之前買入
        past_txns = txns[(txns["symbol"] == sym) & (txns["date_dt"] < ex_date)]
        
        if past_txns.empty:
            continue
            
        shares_held = 0.0
        for _, t in past_txns.iterrows():
            if t["action"] == "BUY":
                shares_held += t["shares"]
            elif t["action"] == "SELL":
                shares_held -= t["shares"]
                
        if shares_held > 0:
            rec_cash = 0.0
            rec_stock = 0.0
            if div["type"] == "CASH":
                rec_cash = shares_held * div["cash_amount"]
                total_cash += rec_cash
            elif div["type"] == "STOCK":
                rec_stock = shares_held * div["stock_ratio"]
                stock_received[sym] = stock_received.get(sym, 0) + rec_stock
                
            details.append({
                "symbol": sym,
                "ex_date": div["ex_date"],
                "type": div["type"],
                "shares_held": shares_held,
                "cash_received": rec_cash,
                "stock_received": rec_stock,
            })
            
    return total_cash, stock_received, details
