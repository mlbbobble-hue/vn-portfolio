"""
提醒條件判斷 + 通知發送模組
支援：Telegram Bot、Line Notify
"""
import requests
import logging
from datetime import datetime, timedelta
from db_router import (get_watchlist, load_notification_settings,
                      update_last_alerted, get_price_cache)
from market_data import get_moving_average
from portfolio import get_estimated_yield, get_dividend_income_summary

logger = logging.getLogger(__name__)

COOLDOWN_HOURS = 4  # 同一股票提醒的冷卻時間（避免洗版）


# ══════════════════════════════════════════════════════════════
#  通知發送
# ══════════════════════════════════════════════════════════════

def send_telegram(message: str, token: str = "", chat_id: str = "") -> bool:
    """發送 Telegram 訊息"""
    if not token or not chat_id:
        settings = load_notification_settings()
        token   = token or settings.get("telegram_token", "")
        chat_id = chat_id or settings.get("telegram_chat_id", "")

    if not token or not chat_id:
        logger.warning("Telegram 未設定 Token 或 Chat ID")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Telegram 發送失敗: {e}")
        return False


def send_line_notify(message: str, token: str = "") -> bool:
    """發送 Line Notify 訊息"""
    if not token:
        settings = load_notification_settings()
        token = settings.get("line_token", "")

    if not token:
        logger.warning("Line Notify 未設定 Token")
        return False

    try:
        r = requests.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {token}"},
            data={"message": message},
            timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Line Notify 發送失敗: {e}")
        return False


def send_notification(message: str) -> dict:
    """
    同時發送 Telegram + Line Notify
    回傳各渠道的發送結果
    """
    settings = load_notification_settings()
    results = {}

    if settings.get("telegram_token") and settings.get("telegram_chat_id"):
        results["telegram"] = send_telegram(message)

    if settings.get("line_token"):
        results["line"] = send_line_notify(message)

    if not results:
        logger.info("未設定任何通知渠道，訊息：" + message)

    return results


# ══════════════════════════════════════════════════════════════
#  提醒條件檢查
# ══════════════════════════════════════════════════════════════

def _is_in_cooldown(last_alerted_str: str | None) -> bool:
    """檢查是否在冷卻時間內"""
    if not last_alerted_str:
        return False
    try:
        last = datetime.fromisoformat(last_alerted_str)
        return (datetime.now() - last) < timedelta(hours=COOLDOWN_HOURS)
    except Exception:
        return False


def check_and_fire_alerts() -> list[dict]:
    """
    檢查所有啟用的提醒條件，對符合條件的股票發送通知
    回傳：觸發提醒的紀錄清單
    """
    watchlist = get_watchlist()
    if watchlist.empty:
        return []

    price_cache = get_price_cache()
    price_map = {}
    if not price_cache.empty:
        price_map = price_cache.set_index("symbol")[["price", "change_pct"]].to_dict("index")

    # 取得配息摘要（用於殖利率計算）
    try:
        symbols = watchlist["symbol"].tolist()
        div_summary = get_dividend_income_summary(symbols)
        div_map = {}
        if not div_summary.empty:
            for _, row in div_summary.iterrows():
                div_map[row["symbol"]] = row["annual_dps"]
    except Exception:
        div_map = {}

    fired = []

    for _, item in watchlist.iterrows():
        if not item.get("alert_enabled", 1):
            continue
        if _is_in_cooldown(item.get("last_alerted")):
            continue

        sym = item["symbol"]
        p_data = price_map.get(sym, {})
        cur_price = p_data.get("price", 0)
        if cur_price <= 0:
            continue

        alerts_for_sym = []

        # ── 1. 目標買入價提醒 ──
        target = item.get("target_price")
        if target and target > 0 and cur_price <= target:
            pct_diff = ((cur_price - target) / target * 100)
            alerts_for_sym.append(
                f"🎯 <b>{sym}</b> 已觸及目標買入價！\n"
                f"   目標價：{target:,.0f} VND\n"
                f"   目前價：{cur_price:,.0f} VND ({pct_diff:+.1f}%)"
            )

        # ── 2. MA60 均線提醒 ──
        if item.get("ma60_alert", 0):
            try:
                ma60 = get_moving_average(sym, 60)
                if ma60 and ma60 > 0:
                    diff_pct = ((cur_price - ma60) / ma60 * 100)
                    if abs(diff_pct) <= 2.0:  # 距離 MA60 ±2% 以內
                        alerts_for_sym.append(
                            f"📊 <b>{sym}</b> 接近季線（MA60）！\n"
                            f"   MA60：{ma60:,.0f} VND\n"
                            f"   目前：{cur_price:,.0f} VND ({diff_pct:+.1f}%)"
                        )
            except Exception as e:
                logger.debug(f"MA60 check failed for {sym}: {e}")

        # ── 3. 殖利率門檻提醒 ──
        yield_thresh = item.get("yield_threshold")
        if yield_thresh and yield_thresh > 0:
            annual_dps = div_map.get(sym, 0)
            if annual_dps > 0:
                est_yield = get_estimated_yield(sym, cur_price, annual_dps)
                if est_yield >= yield_thresh * 100:
                    alerts_for_sym.append(
                        f"💰 <b>{sym}</b> 殖利率達標！\n"
                        f"   預估殖利率：{est_yield:.2f}%\n"
                        f"   設定門檻：{yield_thresh*100:.1f}%\n"
                        f"   目前股價：{cur_price:,.0f} VND"
                    )

        if alerts_for_sym:
            full_msg = "\n\n".join(alerts_for_sym)
            header = (f"🔔 越南股市投資組合提醒\n"
                      f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                      f"{'─'*30}\n\n")
            send_notification(header + full_msg)
            update_last_alerted(sym)
            fired.append({"symbol": sym, "alerts": alerts_for_sym, "price": cur_price})

    return fired


def test_notification() -> dict:
    """發送測試通知，確認設定是否正確"""
    msg = (
        "✅ 越南股市投資組合系統\n"
        "通知功能測試成功！\n"
        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return send_notification(msg)
