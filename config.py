"""
系統設定檔 — 請修改此檔案來設定您的個人化選項
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── 路徑設定 ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "portfolio.db"

# 確保資料目錄存在
DATA_DIR.mkdir(exist_ok=True)

# ── 股價刷新頻率 ──────────────────────────────────────────────
PRICE_REFRESH_SECONDS = 60  # 每 60 秒刷新一次（避免 API 限速）

# ── 券商列表 ──────────────────────────────────────────────────
BROKERS = ["TCBS", "PHS", "VNDIRECT", "SSI", "MBS", "其他"]

# ── Telegram Bot 設定 ─────────────────────────────────────────
# 1. 在 Telegram 找 @BotFather 建立 Bot
# 2. 複製 BOT_TOKEN 貼上
# 3. 傳訊息給 Bot，再到 https://api.telegram.org/bot<TOKEN>/getUpdates 取得 CHAT_ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")   # 例：1234567890:ABC-DEF...
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")     # 例：123456789

# ── Line Notify 設定 ──────────────────────────────────────────
# 前往 https://notify-bot.line.me/my/ 取得個人 Token
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "")

# ── 市場設定 ──────────────────────────────────────────────────
MARKET_OPEN_HOUR  = 9    # 越南股市開盤（UTC+7）
MARKET_CLOSE_HOUR = 15   # 越南股市收盤

# ── 預設觀察股票（用於測試）────────────────────────────────────
DEFAULT_WATCHLIST = ["FPT", "TCB", "HPG", "VEA", "VNM", "MWG"]
