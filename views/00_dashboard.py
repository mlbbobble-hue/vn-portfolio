"""
頁面0：首頁總覽 (Dashboard) - 國泰手機 App 風格
"""
from theme import load_css
load_css()
import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

from i18n import t
from auth_page import check_auth, render_user_info_sidebar
from portfolio import compute_portfolio_with_prices, get_total_realized_pl, compute_received_dividends, compute_historical_equity
from db_router import get_price_cache
from config import PRICE_REFRESH_SECONDS

domain_map = {
    "FPT": "fpt.com.vn",
    "SCS": "saigoncargo.com",
    "VEA": "veam.com.vn",
    "TCB": "techcombank.com",
    "ACB": "acb.com.vn",
    "HPG": "hoaphat.com.vn",
    "MBB": "mbbank.com.vn",
    "BMP": "binhminhplastic.com.vn",
    "VHC": "vinhhoan.com",
    "QNS": "qns.com.vn",
    "VNM": "vinamilk.com.vn",
    "MWG": "thegioididong.com",
    "FRT": "fptretail.com.vn"
}

def get_favicon_url(symbol):
    custom_domains = {
        "VCB": "vietcombank.com.vn",
        "OCB": "ocb.com.vn",
        "VND": "vndirect.com.vn",
        "SSI": "ssi.com.vn",
        "VPB": "vpbank.com.vn",
        "HDB": "hdbank.com.vn",
        "VRE": "vincom.com.vn",
        "VIC": "vingroup.net",
        "VHM": "vinhomes.vn",
        "GAS": "pvgas.com.vn",
        "PLX": "petrolimex.com.vn",
        "POW": "pvpower.vn",
        "SAB": "sabeco.com.vn",
        "VJC": "vietjetair.com",
        "SHB": "shb.com.vn",
        "STB": "sacombank.com.vn",
        "TPB": "tpb.vn",
        "VIB": "vib.com.vn",
        "GVR": "vrg.com.vn",
        "BCM": "becamex.com.vn"
    }
    domain = domain_map.get(symbol) or custom_domains.get(symbol) or f"{symbol.lower()}.com.vn"
    return f"https://www.google.com/s2/favicons?sz=64&domain={domain}"

def clean_html(html_str: str) -> str:
    return "\n".join(line.strip() for line in html_str.split("\n") if line.strip())

st.html(clean_html("""
<style>
/* 針對本頁面的微調 */
.app-title-small { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; display:block; }
.empty-state { text-align: center; padding: 40px 20px; background: var(--bg-card); border-radius: 12px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; color: var(--text-secondary); }
.empty-text { color: var(--text-secondary); font-size: 16px; margin-bottom: 24px; }

/* === Mobile-responsive calendar scroll wrapper === */
.calendar-scroll-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    width: 100%;
    padding-bottom: 8px;
}
.calendar-scroll-wrapper::-webkit-scrollbar {
    height: 5px;
}
.calendar-scroll-wrapper::-webkit-scrollbar-thumb {
    background: rgba(139, 92, 246, 0.4);
    border-radius: 4px;
}
.calendar-inner {
    min-width: 680px;
}

/* Custom Segmented Radio Buttons */
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    background: rgba(30, 41, 59, 0.45) !important;
    padding: 6px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label {
    background: transparent !important;
    border: 1px solid transparent !important;
    padding: 6px 14px !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.2s ease-in-out !important;
    margin: 0 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.5) !important;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15) !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) * {
    color: #ffffff !important;
    font-weight: 700 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] [data-testid="stRadioCircle"] {
    display: none !important;
}
div[data-testid="stRadio"] > label[data-testid="stWidgetLabel"] {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    margin-bottom: 8px !important;
    display: block !important;
}

/* News Cards Styling */
.news-card {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    margin-bottom: 12px !important;
    display: flex !important;
    align-items: flex-start !important;
    gap: 12px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), inset 0 1px 1px rgba(255, 255, 255, 0.05) !important;
}
.news-card:hover {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(139, 92, 246, 0.4) !important;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.15) !important;
    transform: translateY(-2px) !important;
}
.news-badge {
    background: rgba(139, 92, 246, 0.15) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    color: #c084fc !important;
    padding: 4px 10px !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    flex-shrink: 0 !important;
}
.news-badge.held {
    background: rgba(16, 185, 129, 0.15) !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    color: #34d399 !important;
}

/* === Mobile overrides (max-width: 640px) === */
@media (max-width: 640px) {
    /* Radio buttons: each option takes ~half the row */
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 8px 10px !important;
        font-size: 13px !important;
        flex: 1 1 calc(50% - 8px) !important;
        text-align: center !important;
    }
    /* Holding stats: switch from 4-col to 2-col grid */
    .holding-stats-grid {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    /* News card: stack badge above title */
    .news-card {
        flex-direction: column !important;
        gap: 8px !important;
        padding: 12px !important;
    }
    /* Tighter detail card padding on mobile */
    .detail-card {
        padding: 14px 14px !important;
    }
    /* Scroll hint label */
    .calendar-scroll-hint {
        display: block !important;
    }
}
@media (min-width: 641px) {
    .calendar-scroll-hint { display: none !important; }
}
</style>
"""))


if not check_auth():
    st.stop()

# 獲取資料



holdings = compute_portfolio_with_prices()

# 過濾掉債券 (Bonds don't need to be in the earnings calendar/corporate reports)
if not holdings.empty:
    try:
        from db_router import get_all_transactions
        txns = get_all_transactions()
        if not txns.empty and "note" in txns.columns:
            bond_symbols = set(txns[txns["note"].str.contains(r"\[BOND\]", case=False, na=False)]["symbol"].unique())
            holdings = holdings[~holdings["symbol"].isin(bond_symbols)]
    except Exception:
        pass

total_value = 0.0
total_cost = 0.0
total_unrealized = 0.0
roi_pct = 0.0

if not holdings.empty:
    total_value = holdings["market_value"].sum()
    total_cost = holdings["total_cost"].sum()
    total_unrealized = holdings["unrealized_pl"].sum()
    roi_pct = (total_unrealized / total_cost * 100) if total_cost > 0 else 0.0

is_loading_prices = not holdings.empty and total_value == 0 and total_cost > 0

if is_loading_prices:
    st_autorefresh(interval=2000, limit=15, key="wait_for_prices")


def render_watchlist_manager(lang, held_symbols):
    if "manual_added_symbols" not in st.session_state:
        st.session_state["manual_added_symbols"] = []
        
    POPULAR_SYMBOLS = [
        "ACB", "BCM", "BID", "BMP", "BVH", "CTG", "DGC", "DIG", "DXG", 
        "FPT", "FRT", "GAS", "GVR", "HAX", "HDB", "HPG", "HSG", "KBC", 
        "MBB", "MSN", "MWG", "NKG", "NLG", "NT2", "OCB", "PLX", "POW", 
        "PVD", "PVS", "QNS", "SAB", "SCS", "SHB", "SSB", "SSI", "STB", 
        "TCB", "TPB", "VCB", "VEA", "VHC", "VHM", "VIC", "VJC", "VND", 
        "VNM", "VPB", "VRE"
    ]
    
    expander_title = "🔍 手動新增其他追蹤股票 (Add other stocks)" if lang == "zh" else "🔍 Thêm cổ phiếu theo dõi khác"
    with st.expander(expander_title, expanded=False):
        ms_options = sorted(list(set(POPULAR_SYMBOLS + st.session_state["manual_added_symbols"]) - set(held_symbols)))
        selected_additional = st.multiselect(
            "選擇要顯示的股票 (Select stocks to display)" if lang == "zh" else "Chọn cổ phiếu muốn hiển thị",
            options=ms_options,
            default=[sym for sym in st.session_state["manual_added_symbols"] if sym in ms_options],
            key="calendar_additional_stocks_ms"
        )
        st.session_state["manual_added_symbols"] = selected_additional
        
        col_add1, col_add2 = st.columns([7, 3])
        with col_add1:
            custom_sym = st.text_input(
                "➕ 輸入自訂代號 (Add custom ticker)" if lang == "zh" else "➕ Nhập mã tự chọn",
                key="custom_ticker_input",
                placeholder="例如 / e.g., AAA"
            ).strip().upper()
        with col_add2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("新增 (Add)" if lang == "zh" else "Thêm", use_container_width=True, key="add_custom_ticker_btn"):
                if custom_sym:
                    if custom_sym in held_symbols:
                        st.warning(f"{custom_sym} 已在您的持股中" if lang == "zh" else f"{custom_sym} đã có trong danh mục")
                    elif custom_sym in st.session_state["manual_added_symbols"]:
                        st.info(f"{custom_sym} 已在追蹤清單中" if lang == "zh" else f"{custom_sym} đã được theo dõi")
                    else:
                        st.session_state["manual_added_symbols"].append(custom_sym)
                        st.rerun()


def show_earnings_calendar(lang="zh", is_empty=False):
    # 1. Base events definition
    base_events = {
        15: [{"symbol": "FPT", "color": "#FF8C00"}],
        16: [{"symbol": "SCS", "color": "#00F0FF"}],
        17: [{"symbol": "VEA", "color": "#FF2A85"}],
        20: [{"symbol": "TCB", "color": "#00F0FF"}],
        21: [{"symbol": "ACB", "color": "#00F0FF"}],
        22: [{"symbol": "HPG", "color": "#FF8C00"}],
        23: [{"symbol": "MBB", "color": "#00F0FF"}],
        24: [{"symbol": "BMP", "color": "#FF2A85"}],
        27: [{"symbol": "VHC", "color": "#FF8C00"}],
        28: [{"symbol": "QNS", "color": "#FF2A85"}],
        29: [{"symbol": "VNM", "color": "#FF2A85"}],
        30: [{"symbol": "MWG", "color": "#FF8C00"}],
        31: [{"symbol": "FRT", "color": "#FF8C00"}]
    }

    # Grids for the 4 quarters
    grid_q1 = [
        [None, None, 1, 2, 3],
        [6, 7, 8, 9, 10],
        [13, 14, 15, 16, 17],
        [20, 21, 22, 23, 24],
        [27, 28, 29, 30, None]
    ]
    grid_q2 = [
        [None, None, 1, 2, 3],
        [6, 7, 8, 9, 10],
        [13, 14, 15, 16, 17],
        [20, 21, 22, 23, 24],
        [27, 28, 29, 30, 31]
    ]
    grid_q3 = [
        [None, None, None, 1, 2],
        [5, 6, 7, 8, 9],
        [12, 13, 14, 15, 16],
        [19, 20, 21, 22, 23],
        [26, 27, 28, 29, 30]
    ]
    grid_q4 = [
        [None, None, None, None, 1],
        [4, 5, 6, 7, 8],
        [11, 12, 13, 14, 15],
        [18, 19, 20, 21, 22],
        [25, 26, 27, 28, 29]
    ]
    
    headers = ["MON", "TUE", "WED", "THU", "FRI"]
    if lang == "zh":
        headers = ["週一 (Mon)", "週二 (Tue)", "週三 (Wed)", "週四 (Thu)", "週五 (Fri)"]
        
    st.markdown("""<style>
.calendar-container {
    background: var(--bg-card);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-soft);
}
.calendar-title {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.calendar-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
    background: rgba(255, 255, 255, 0.02);
    padding: 8px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
}
.calendar-header-cell {
    text-align: center;
    font-weight: bold;
    color: var(--text-secondary);
    font-size: 11px;
    padding: 4px 0;
    border-bottom: 1px solid var(--border-color);
}
.calendar-day-cell {
    background: rgba(255, 255, 255, 0.01);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    min-height: 70px;
    padding: 4px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    transition: all 0.2s;
}
.calendar-day-cell:hover {
    background: rgba(255, 255, 255, 0.03);
    border-color: #9D4EDD;
}
.calendar-empty-cell {
    background: transparent;
    border: 1px solid transparent;
    min-height: 70px;
}
.calendar-day-num {
    font-size: 10px;
    color: #64748b;
    font-weight: bold;
    margin-bottom: 2px;
}
.calendar-stock-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 8px;
    border-radius: 6px;
    text-decoration: none !important;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    margin-top: 2px;
}
.calendar-stock-tag:hover {
    transform: translateY(-1px);
    border-color: #00F0FF !important;
    box-shadow: 0 0 8px rgba(0, 240, 255, 0.3);
}
.calendar-tag-text {
    font-size: 11px;
    font-weight: bold;
    color: #ffffff;
    vertical-align: middle;
}
</style>""", unsafe_allow_html=True)

    # Fetch held symbols
    held_symbols = []
    if not is_empty:
        try:
            held_symbols = holdings[holdings["total_shares"] > 0]["symbol"].tolist()
        except:
            pass

    def get_symbol_day(symbol, q_key):
        peak_days = {
            "Q1": [15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30],
            "Q2": [15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31],
            "Q3": [15, 16, 19, 20, 21, 22, 23, 26, 27, 28, 29, 30],
            "Q4": [15, 16, 19, 20, 21, 22, 23, 26, 27, 28, 29, 30]
        }
        days_list = peak_days.get(q_key, [15, 20, 25])
        idx = sum(ord(c) for c in symbol) % len(days_list)
        return days_list[idx]

    def get_quarter_events(q_key, held_list, additional_list):
        events_map = {}
        all_symbols = list(dict.fromkeys(held_list + additional_list))
        
        base_sym_info = {}
        for day, evs in base_events.items():
            for ev in evs:
                base_sym_info[ev["symbol"]] = {
                    "day": day,
                    "color": ev["color"]
                }
                
        for sym in all_symbols:
            is_held = sym in held_list
            if sym in base_sym_info:
                day = base_sym_info[sym]["day"]
                color = "#10B981" if is_held else base_sym_info[sym]["color"]
            else:
                day = get_symbol_day(sym, q_key)
                color = "#10B981" if is_held else "#00F0FF"
                
            max_days = {"Q1": 30, "Q2": 31, "Q3": 30, "Q4": 29}
            limit_day = max_days.get(q_key, 30)
            target_day = day if day <= limit_day else limit_day
            
            if target_day not in events_map:
                events_map[target_day] = []
            events_map[target_day].append({
                "symbol": sym,
                "color": color,
                "is_holding": is_held
            })
        return events_map

    # 2. Parse URL query parameters to maintain selection state
    query_params = st.query_params
    selected_stock_param = query_params.get("select_stock", None)
    q_tab_param = query_params.get("q_tab", "Q2")  # Default to Q2

    q_options = ["Q1", "Q2", "Q3", "Q4"]
    default_idx = q_options.index(q_tab_param) if q_tab_param in q_options else 1

    # Segmented Radio selector for Quarters
    q_key = st.radio(
        "📅 選擇財報季度" if lang == "zh" else "📅 Chọn quý công báo BCTC",
        options=q_options,
        index=default_idx,
        format_func=lambda x: {
            "Q1": "🌸 Q1 財報季 (4月) - 已發布" if lang == "zh" else "🌸 Mùa BCTC Q1 (T4) - Đã phát hành",
            "Q2": "🔥 Q2 財報季 (7月) - 預估中" if lang == "zh" else "🔥 Mùa BCTC Q2 (T7) - Dự báo",
            "Q3": "🍁 Q3 財報季 (10月) - 預估中" if lang == "zh" else "🍁 Mùa BCTC Q3 (T10) - Dự báo",
            "Q4": "❄️ Q4/全年 財報季 (1月) - 預估中" if lang == "zh" else "❄️ Mùa BCTC Q4/Cả năm (T1) - Dự báo"
        }[x],
        horizontal=True,
        key=f"calendar_quarter_radio_{'empty' if is_empty else 'full'}"
    )

    details_q1 = {
        "FPT": {"type": "科技與外包" if lang == "zh" else "Công nghệ", "actual_growth": "YoY +19.4%", "desc": "Q1 營收 14,093 億 VND，淨利 2,160 億 VND。受惠於海外軟體外包訂單爆發與 AI 封測佈局，獲利持續穩健成長。" if lang == "zh" else "Doanh thu Q1 đạt 14.093 tỷ VND, LNST đạt 2.160 tỷ VND. Tăng trưởng mạnh từ mảng xuất khẩu phần mềm và chuyển đổi số."},
        "SCS": {"type": "航空物流" if lang == "zh" else "Logistics", "actual_growth": "YoY +29.8%", "desc": "Q1 營收 212 億 VND，淨利 148 億 VND。進出口貿易回溫，空運貨量大增，毛利率維持在 75% 的超高水準。" if lang == "zh" else "Doanh thu Q1 đạt 212 tỷ VND, LNST đạt 148 tỷ VND. Sản lượng hàng hóa sân bay phục hồi mạnh mẽ, biên lợi nhuận cực cao."},
        "VEA": {"type": "汽車製造" if lang == "zh" else "Sản xuất ô tô", "actual_growth": "YoY -4.0%", "desc": "Q1 淨利 1,350 億 VND。本田與豐田銷量微幅下滑，但聯營公司投資收益仍極為充沛，提供強大的分紅防禦力。" if lang == "zh" else "LNST Q1 đạt 1.350 tỷ VND. Doanh số Honda & Toyota giảm nhẹ nhưng nguồn thu từ liên doanh liên kết vẫn rất dồi dào."},
        "TCB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "actual_growth": "YoY +38.7%", "desc": "Q1 營收 12,200 億 VND，淨利 7,800 億 VND。手續費與信貸成長超越預期，且地產復甦使壞帳撥備回撥，淨利爆發。" if lang == "zh" else "LNST Q1 đạt 7.800 tỷ VND. Tăng trưởng tín dụng mạnh mẽ kết hợp hoàn nhập dự phòng từ sự phục hồi của BĐS."},
        "ACB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "actual_growth": "YoY +1.9%", "desc": "Q1 營收 8,100 億 VND，淨利 4,900 億 VND。零售金融與消費貸信貸增長持平，壞帳控制全越第一，獲利保持平穩。" if lang == "zh" else "LNST Q1 đạt 4.900 tỷ VND. ACB kiểm soát tốt nợ xấu và duy trì sự ổn định cao trong hoạt động cốt lõi."},
        "HPG": {"type": "鋼鐵工業" if lang == "zh" else "Thép & Vật liệu", "actual_growth": "YoY +700%+", "desc": "Q1 營收 31,000 億 VND，淨利 2,869 億 VND。去年同期基期極低，隨鋼鐵內需回溫與煤炭成本下滑，獲利呈現爆發式增長。" if lang == "zh" else "LNST Q1 đạt 2.869 tỷ VND, tăng gấp nhiều lần cùng kỳ nhờ giá bán thép phục hồi và giá nguyên liệu đầu vào hạ nhiệt."},
        "MBB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "actual_growth": "YoY -11.0%", "desc": "Q1 營收 11,900 億 VND，淨利 5,795 億 VND。因支持體系弱勢銀行以及部分壞帳提撥增加，獲利較去年同期微幅下滑。" if lang == "zh" else "LNST Q1 đạt 5.795 tỷ VND. Lợi nhuận giảm nhẹ do tăng trích lập dự phòng rủi ro nợ xấu."},
        "BMP": {"type": "建材製造" if lang == "zh" else "VLXD", "actual_growth": "YoY -33.0%", "desc": "Q1 營收 1,002 億 VND，淨利 190 億 VND。主因 PVC 原料價格上漲與首季建材需求較淡，但帳上現金充裕仍將維持高分紅。" if lang == "zh" else "LNST Q1 đạt 190 tỷ VND. Biên lợi nhuận gộp chịu áp lực do giá hạt nhựa PVC biến động tăng."},
        "VHC": {"type": "海鮮出口" if lang == "zh" else "Thủy hải sản", "actual_growth": "YoY -22.0%", "desc": "Q1 營收 2,729 億 VND，淨利 170 億 VND。美國市場庫存去化比預期慢，出口均價偏低，導致首季獲利下滑。" if lang == "zh" else "LNST Q1 đạt 170 tỷ VND. Doanh số xuất khẩu cá tra gặp khó khăn về giá bán bình quan tại thị trường Mỹ."},
        "QNS": {"type": "食品飲料" if lang == "zh" else "Thực phẩm", "actual_growth": "YoY +68.0%", "desc": "Q1 營收 2,520 億 VND，淨利 532 億 VND。受惠於國際糖價維持高檔、自產原糖利潤改善以及豆奶剛需強勁，獲利大增。" if lang == "zh" else "LNST Q1 đạt 532 tỷ VND. Mảng đường ghi nhận biên lợi nhuận gộp bứt phá nhờ giá đường Neo ở mức cao."},
        "VNM": {"type": "食品飲料" if lang == "zh" else "Thực phẩm", "actual_growth": "YoY +16.0%", "desc": "Q1 營收 14,100 億 VND，淨利 2,207 億 VND。奶粉與液態奶內銷回溫，海外附屬公司銷量穩增，防禦型業績出色。" if lang == "zh" else "LNST Q1 đạt 2.207 tỷ VND. Doanh thu nội địa ổn định kết hợp tối ưu hóa chi phí nguyên liệu sữa bột nhập khẩu."},
        "MWG": {"type": "民生零售" if lang == "zh" else "Bán lẻ", "actual_growth": "YoY +4200%+", "desc": "Q1 營收 31,480 億 VND，淨利 902 億 VND。旗下「百家綠」生鮮超市損益平衡點改善，「行動世界」手機店毛利大幅回升。" if lang == "zh" else "LNST Q1 đạt 902 tỷ VND. Chuỗi Bách Hóa Xanh cải thiện mạnh doanh số trung bình cửa hàng, đưa lợi nhuận hồi sinh ngoạn mục."},
        "FRT": {"type": "醫藥零售" if lang == "zh" else "Bán lẻ dược phẩm", "actual_growth": "YoY +300%+", "desc": "Q1 營收 9,040 億 VND，淨利 61 億 VND。龍洲藥局連鎖店數增至 1,600 家，單店坪效維持高檔，正式進入獲利貢獻期。" if lang == "zh" else "LNST Q1 đạt 61 tỷ VND. Chuỗi nhà thuốc Long Châu tiếp tục là động lực tăng trưởng cốt lõi với doanh thu bùng nổ."},
        "HAX": {"type": "汽車銷售" if lang == "zh" else "Phân phối ô tô", "actual_growth": "YoY -8.0%", "desc": "Q1 營收 1,098 億 VND (YoY +14%)，淨利 153 億 VND (YoY -8%)。受豪華車市場價格戰與利息支出增加影響，本業利潤下滑，但因代理商返利與獎金挹注維持獲利。" if lang == "zh" else "Doanh thu Q1 đạt 1.098 tỷ VND (YoY +14%), LNST đạt 15.3 tỷ VND (YoY -8%). Áp lực cạnh tranh giá bán xe sang và chi phí tài chính bào mòn lợi nhuận cốt lõi."},
        "OCB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "actual_growth": "YoY +37.0%", "desc": "Q1 營收 2,722 億 VND (YoY +19.8%)，稅前淨利 1,224 億 VND (YoY +37%)。信貸投放量首度突破 200 兆 VND，且手續費與淨利差控制良好，推動獲利強勁增長。" if lang == "zh" else "Tổng thu thuần Q1 đạt 2.722 tỷ VND (YoY +19.8%), LNTT đạt 1.224 tỷ VND (YoY +37%). Dư nợ tín dụng lần đầu vượt mốc 200 nghìn tỷ VND."},
        "NT2": {"type": "電力能源" if lang == "zh" else "Điện lực", "actual_growth": "YoY +387.0%", "desc": "Q1 營收 2,172 億 VND (YoY +52%)，淨利 180 億 VND (YoY +387%)。受惠於氣候乾旱使火力發電需求大增，且發電設備折舊完畢使折舊費用銳減，獲利呈爆發性成長。" if lang == "zh" else "Doanh thu Q1 đạt 2.172 tỷ VND (YoY +52%), LNST đạt 180 tỷ VND (YoY +387%). Sản lượng huy động tăng mạnh và chi phí khấu hao giảm sau khi hoàn tất khấu hao."}
    }

    details_base = {
        "FPT": {"type": "科技與外包" if lang == "zh" else "Công nghệ", "expected_growth": "YoY +22%", "desc": "越南科技業霸主。軟體出口訂單飽滿，AI 封測業務發酵，預期獲利穩定高成長。" if lang == "zh" else "Đơn hàng xuất khẩu phần mềm dồi dào, doanh thu tăng trưởng hai con số vững chắc."},
        "SCS": {"type": "航空物流" if lang == "zh" else "Logistics", "expected_growth": "YoY +18%", "desc": "新山一機場航空貨運壟斷者。受惠進出口貿易回溫，毛利率維持在 70% 以上高檔。" if lang == "zh" else "Độc quyền dịch vụ hàng hóa sân bay Tân Sơn Nhất, biên lợi nhuận ròng rất cao."},
        "VEA": {"type": "汽車製造" if lang == "zh" else "Sản xuất ô tô", "expected_growth": "YoY +12%", "desc": "持有本田、豐田、福特大筆股權。聯營公司銷量回穩，預期派發高額現金股利。" if lang == "zh" else "Nguồn thu từ liên doanh Honda, Toyota dồi dào, duy trì chia cổ tức cao."},
        "TCB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "expected_growth": "YoY +25%", "desc": "私營銀行龍頭。受惠於房地產復甦與手續費收入成長，信貸增長強勁。" if lang == "zh" else "Hồi phục tín dụng mạnh mẽ và đóng góp tốt từ mảng bán lẻ."},
        "ACB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "expected_growth": "YoY +20%", "desc": "風控模範生。壞帳率極低，零售與消費金融信貸需求穩健，利潤率持平。" if lang == "zh" else "Tỷ lệ nợ xấu ở mức rất thấp, kiểm soát rủi ro hàng đầu hệ thống."},
        "HPG": {"type": "鋼鐵工業" if lang == "zh" else "Thép & Vật liệu", "expected_growth": "YoY +150%+", "desc": "鋼鐵龍頭。隨內需與基建鋼鐵需求復甦，加上榕橘二期預期產出，利潤比去年同期爆發式增長。" if lang == "zh" else "Biên lợi nhuận phục hồi mạnh mẽ từ đáy, công suất lò cao được khai thác tối đa."},
        "MBB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "expected_growth": "YoY +15%", "desc": "軍方背景大行。數位化用戶持續增長，淨利差(NIM)維持優勢。" if lang == "zh" else "Ngân hàng TMCP Quân đội, quy mô tệp khách hàng số tăng trưởng ấn tượng."},
        "BMP": {"type": "建材製造" if lang == "zh" else "VLXD", "expected_growth": "YoY +10%", "desc": "平明塑膠。主要原料 PVC 價格維持低檔，預期毛利率維持高點，分紅極高。" if lang == "zh" else "Biên lợi nhuận gộp duy trì mức cao nhờ giá hạt nhựa đầu vào thấp."},
        "VHC": {"type": "海鮮出口" if lang == "zh" else "Thủy hải sản", "expected_growth": "YoY +35%", "desc": "查魚出口女王。美國市場庫存去化完畢，下半年出口訂單顯著回溫。" if lang == "zh" else "Đơn hàng xuất khẩu cá tra sang Mỹ và EU hồi phục tích cực."},
        "QNS": {"type": "食品飲料" if lang == "zh" else "Thực phẩm", "expected_growth": "YoY +15%", "desc": "豆奶與糖業龍頭。夏季飲品剛性需求強，製糖業務受惠於國際糖價高檔。" if lang == "zh" else "Thương hiệu sữa đậu nành Fami dẫn đầu thị phần, mảng đường hoạt động tốt."},
        "VNM": {"type": "食品飲料" if lang == "zh" else "Thực phẩm", "expected_growth": "YoY +8%", "desc": "越南牛奶。內需民生消費防禦型標的，海外市場（中東）銷量成長。" if lang == "zh" else "Sữa Vinamilk phòng thủ tốt, dòng tiền mạnh chia cổ tức đều đặn."},
        "MWG": {"type": "民生零售" if lang == "zh" else "Bán lẻ", "expected_growth": "YoY +120%+", "desc": "零售巨頭。旗下「百家綠」生鮮超市正式轉盈，手機店利潤率改善，獲利大幅翻倍。" if lang == "zh" else "Bách Hóa Xanh bắt đầu hòa vốn và có lãi, kéo lợi nhuận tập đoàn tăng vọt."},
        "FRT": {"type": "醫藥零售" if lang == "zh" else "Bán lẻ dược phẩm", "expected_growth": "YoY +90%+", "desc": "龍洲藥局快速擴張並進入收割期。連鎖藥局獲利成長顯著，帶動 FRT 營收大增。" if lang == "zh" else "Chuỗi nhà thuốc Long Châu tiếp tục bứt phá mạnh mẽ làm động lực tăng trưởng chính."},
        "HAX": {"type": "汽車銷售" if lang == "zh" else "Phân phối ô tô", "expected_growth": "YoY +15%", "desc": "越南 Mercedes-Benz 最大代理商。隨豪華車稅收優惠與代理品牌擴展，本業獲利預期迎來復甦。" if lang == "zh" else "Nhà phân phối Mercedes-Benz lớn nhất VN. Kỳ vọng doanh số xe sang phục hồi mạnh nhờ chính sách phí trước bạ."},
        "OCB": {"type": "金融銀行" if lang == "zh" else "Ngân hàng", "expected_growth": "YoY +28%", "desc": "中型私營商業銀行。積極布局零售與數位金融，信貸成長強勁，資產規模持續擴張。" if lang == "zh" else "Ngân hàng TMCP Phương Đông. Tập trung mạnh vào chuyển đổi số và bán lẻ, tăng trưởng tín dụng cao."},
        "NT2": {"type": "電力能源" if lang == "zh" else "Điện lực", "expected_growth": "YoY +12%", "desc": "仁澤二期天然氣發電廠。發電設備陸續折舊完畢，現金流極為充沛，可持續提供穩定且高額的現金股利。" if lang == "zh" else "Nhà máy Điện khí Nhơn Trạch 2. Dòng tiền cực kỳ dồi dào sau khi hết khấu hao thiết bị, duy trì cổ tức tiền mặt cao."}
    }

    if "manual_added_symbols" not in st.session_state:
        st.session_state["manual_added_symbols"] = []

    # Render selected quarter content
    q_events = get_quarter_events(q_key, held_symbols, st.session_state["manual_added_symbols"])
    
    grid_map = {
        "Q1": (grid_q1, "📅 2026年4月份 - 第一季 (Q1) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q1 - Tháng 04/2026"),
        "Q2": (grid_q2, "📅 2026年7月份 - 第二季 (Q2) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q2 - Tháng 07/2026"),
        "Q3": (grid_q3, "📅 2026年10月份 - 第三季 (Q3) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q3 - Tháng 10/2026"),
        "Q4": (grid_q4, "📅 2027年1月份 - 第四季及全年 (Q4) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q4/Cả năm - Tháng 01/2027")
    }
    
    selected_grid, title_str = grid_map.get(q_key, (grid_q2, ""))
    
    # 2. Render Calendar Grid in Python using st.columns
    st.markdown(f"<h3 style='margin-top: 10px; margin-bottom: 18px; color: #ffffff; font-size: 20px; font-weight: bold;'>{title_str}</h3>", unsafe_allow_html=True)
    
    # CSS injection for columns and buttons
    css_rules = [
        """
        /* Desktop grid cell styles */
        .st-key-calendar_grid_container div[data-testid="column"]:has(.calendar-day-num) {
            background: rgba(20, 30, 50, 0.65) !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 10px !important;
            min-height: 145px !important;
            padding: 12px !important;
            transition: all 0.25s ease-in-out !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.08), 0 4px 8px -1px rgba(0, 0, 0, 0.3) !important;
        }
        .st-key-calendar_grid_container div[data-testid="column"]:has(.calendar-day-num):hover {
            background: rgba(30, 41, 59, 0.80) !important;
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 16px rgba(139, 92, 246, 0.35) !important;
        }
        .st-key-calendar_grid_container .stButton {
            display: block !important;
            width: 100% !important;
            margin-top: 4px !important;
            margin-bottom: 4px !important;
        }
        .calendar-header-cell {
            text-align: center;
            font-weight: 700;
            color: #f1f5f9;
            font-size: 15px;
            padding: 12px 0;
            background: rgba(99, 102, 241, 0.2);
            border-radius: 8px;
            border: 1px solid rgba(139, 92, 246, 0.35);
            margin-bottom: 10px;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .calendar-day-num {
            font-size: 15px;
            color: #e2e8f0;
            font-weight: 800;
            margin-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.20);
            padding-bottom: 5px;
        }
        div[data-testid="stExpander"] {
            background: rgba(30, 41, 59, 0.35) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important;
            margin-bottom: 15px !important;
        }
        div[data-testid="stExpander"] details {
            border: none !important;
        }
        div[data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: #e2e8f0 !important;
            padding: 8px 12px !important;
        }
        """
    ]
    
    # Generate button-specific styles for favicons and border colors
    for day, evs in q_events.items():
        for ev in evs:
            sym = ev["symbol"]
            color_bg = ev["color"]
            favicon_url = get_favicon_url(sym)
            
            rule = f"""
            /* DESKTOP GRID BUTTON */
            .st-key-btn_grid_{q_key}_{day}_{sym} button {{
                width: 100% !important;
                background: {color_bg}18 !important;
                border: 1px solid {color_bg}55 !important;
                color: #ffffff !important;
                padding-left: 38px !important;
                padding-right: 8px !important;
                padding-top: 6px !important;
                padding-bottom: 6px !important;
                min-height: 36px !important;
                height: 36px !important;
                font-size: 14px !important;
                font-weight: bold !important;
                background-image: url("{favicon_url}") !important;
                background-repeat: no-repeat !important;
                background-position: 12px center !important;
                background-size: 18px 18px !important;
                border-radius: 8px !important;
                transition: all 0.2s ease-in-out !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            }}
            .st-key-btn_grid_{q_key}_{day}_{sym} button div[data-testid="stMarkdownContainer"] {{
                width: 100% !important;
            }}
            .st-key-btn_grid_{q_key}_{day}_{sym} button p {{
                text-align: left !important;
                margin: 0 !important;
            }}
            .st-key-btn_grid_{q_key}_{day}_{sym} button:hover {{
                border-color: #00F0FF !important;
                background: {color_bg}30 !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 10px rgba(0, 240, 255, 0.2) !important;
            }}

            /* MOBILE 2-COLUMN PILL BUTTON */
            .st-key-btn_list_{q_key}_{day}_{sym} button {{
                width: 100% !important;
                background: {color_bg}15 !important;
                border: 1px solid {color_bg}40 !important;
                color: #ffffff !important;
                padding-left: 34px !important;
                padding-right: 6px !important;
                min-height: 42px !important;
                height: 42px !important;
                background-image: url("{favicon_url}") !important;
                background-repeat: no-repeat !important;
                background-position: 10px center !important;
                background-size: 18px 18px !important;
                border-radius: 8px !important;
                position: relative !important;
                transition: all 0.2s ease-in-out !important;
            }}
            .st-key-btn_list_{q_key}_{day}_{sym} button div[data-testid="stMarkdownContainer"] {{
                width: 100% !important;
            }}
            .st-key-btn_list_{q_key}_{day}_{sym} button p {{
                text-align: left !important;
                font-size: 14.5px !important;
                font-weight: 600 !important;
                margin: 0 !important;
            }}
            .st-key-btn_list_{q_key}_{day}_{sym} button:hover, .st-key-btn_list_{q_key}_{day}_{sym} button:active {{
                border-color: #00F0FF !important;
                background: {color_bg}30 !important;
                transform: translateY(-1px) !important;
            }}
            """
            css_rules.append(rule)
            
    # Auto-switch for Mobile Layout (Hide Grid on mobile, Hide List on desktop)
    css_rules.append("""
        @media (max-width: 640px) {
            .st-key-calendar_grid_container { display: none !important; }
            .st-key-calendar_list_container { display: block !important; }

            /* Force the day group to be a flex container with wrapping */
            [class*="st-key-mob_day_group_"] > div[data-testid="stVerticalBlock"] {
                display: flex !important;
                flex-wrap: wrap !important;
                flex-direction: row !important;
                gap: 8px !important;
                padding-bottom: 16px !important;
            }
            
            /* Each button container takes 50% minus half the gap */
            [class*="st-key-mob_day_group_"] > div[data-testid="stVerticalBlock"] > div.element-container {
                width: calc(50% - 4px) !important;
                flex: 0 0 calc(50% - 4px) !important;
            }

            /* Ensure internal Streamlit div stretches full width of the 50% container */
            [class*="st-key-btn_list_"] {
                width: 100% !important;
            }
        }
        @media (min-width: 641px) {
            .st-key-calendar_grid_container { display: block !important; }
            .st-key-calendar_list_container { display: none !important; }
        }
    """)
            
    st.markdown(f"<style>{''.join(css_rules)}</style>", unsafe_allow_html=True)
    
    def render_content(ev, day, sym):
        if q_key == "Q1":
            raw = details_q1.get(sym) or details_base.get(sym)
        else:
            raw = details_base.get(sym)

        if raw:
            gk = ("淨利成長" if lang == "zh" else "Tăng trưởng LNST") if q_key == "Q1" else ("預期成長" if lang == "zh" else "Tăng trưởng dự kiến")
            gv = raw.get("actual_growth") or raw.get("expected_growth", "—")
            stype = raw.get("type", "")
            desc = raw.get("desc", "")
        else:
            gk = "財報狀態" if lang == "zh" else "BCTC"
            gv = "已發布" if q_key == "Q1" else "預計"
            stype = "持股中" if ev.get("is_holding") else "追蹤中"
            desc = ""

        yr_mo = {"Q1": "2026-04", "Q2": "2026-07", "Q3": "2026-10", "Q4": "2027-01"}.get(q_key, "2026-07")
        dl = "實際發布" if (q_key == "Q1" and lang == "zh") else ("Ngày công bố" if q_key == "Q1" else ("預計發布" if lang == "zh" else "Dự kiến"))
        gneg = "-" in gv or "giảm" in gv.lower()
        gc = "#f87171" if gneg else "#34d399"
        held_badge = "✅ 持股中" if ev.get("is_holding") else ""
        st.markdown(f"**{sym}** {held_badge}  \n*{stype}*")
        st.markdown(f"📅 **{dl}**: `{yr_mo}-{day:02d}`")
        st.markdown(f"🚀 **{gk}**: :{('green' if not gneg else 'red')}[{gv}]")
        if desc:
            st.caption(desc)
        # Holdings stats
        if ev.get("is_holding") and not holdings.empty:
            rows = holdings[holdings["symbol"] == sym]
            if not rows.empty:
                r = rows.iloc[0]
                sh = r["total_shares"]; co = r["total_cost"]
                va = r["market_value"]; un = r["unrealized_pl"]
                pp = (un / co * 100) if co > 0 else 0.0
                c1, c2 = st.columns(2)
                c1.metric("持股數" if lang == "zh" else "SL", f"{sh:,.0f}")
                c2.metric("市值" if lang == "zh" else "GT TT", f"{va:,.0f}")
                c3, c4 = st.columns(2)
                c3.metric("成本" if lang == "zh" else "Vốn", f"{co/sh:,.0f}" if sh > 0 else "—")
                c4.metric("未實現損益" if lang == "zh" else "LNTT", f"{un:+,.0f}", delta=f"{pp:+.2f}%")

    def render_popover(ev, day, sym):
        star = " ⭐" if ev.get("is_holding") else ""
        btn_label = f"{sym}{star}"
        with st.popover(btn_label, use_container_width=True):
            render_content(ev, day, sym)

    @st.dialog("財報詳情" if lang == "zh" else "Earnings Details")
    def show_details_dialog(ev, day, sym):
        render_content(ev, day, sym)

    with st.container(key="calendar_grid_container"):
        # Header row
        cols = st.columns(5, gap="small")
        for col_idx, h in enumerate(headers):
            cols[col_idx].markdown(f"<div class='calendar-header-cell'>{h}</div>", unsafe_allow_html=True)

        # Day rows — stock buttons use st.popover() for inline detail card
        for week in selected_grid:
            cols = st.columns(5, gap="small")
            for col_idx, day in enumerate(week):
                with cols[col_idx]:
                    if day is not None:
                        st.markdown(f"<div class='calendar-day-num'>{day:02d}</div>", unsafe_allow_html=True)
                        if day in q_events:
                            for ev in q_events[day]:
                                sym = ev["symbol"]
                                with st.container(key=f"btn_grid_{q_key}_{day}_{sym}"):
                                    render_popover(ev, day, sym)

    with st.container(key="calendar_list_container"):
        day_labels_zh = {"Mon": "週一", "Tue": "週二", "Wed": "週三", "Thu": "週四", "Fri": "週五"}
        day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        
        has_any = False
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
        with st.expander("📅 點此展開財報日曆" if lang == "zh" else "📅 Expand Earnings Calendar", expanded=False):
            for week in selected_grid:
                for col_idx, day in enumerate(week):
                    if day is not None and day in q_events:
                        has_any = True
                        day_name = day_names_en[col_idx]
                        day_label = f"{day_labels_zh.get(day_name, day_name)} {day:02d}日" if lang == "zh" else f"{day_name} {day:02d}"
                        
                        st.markdown(f"<div style='font-size:15px;font-weight:800;color:#a5b4fc;margin-top:16px;margin-bottom:0px;padding-left:12px;'>{day_label}</div>", unsafe_allow_html=True)
                        with st.container(key=f"mob_day_group_{q_key}_{day}"):
                            for ev in q_events[day]:
                                sym = ev["symbol"]
                                star = " ⭐" if ev.get("is_holding") else ""
                                btn_label = f"{sym}{star}"
                                with st.container(key=f"btn_list_{q_key}_{day}_{sym}"):
                                    if st.button(btn_label, key=f"btn_trigger_list_{q_key}_{day}_{sym}", use_container_width=True):
                                        show_details_dialog(ev, day, sym)
            
            if not has_any:
                st.info("📅 目前季度日曆為空" if lang == "zh" else "📅 No events this quarter")

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)



    




if holdings.empty:
    st.markdown(f'''
    <div class="empty-state">
        <div class="empty-icon">🌱</div>
        <div class="empty-text">{t("portfolio_empty_desc")}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    if st.button(t("go_to_add_tx"), use_container_width=True):
        st.switch_page("views/02_transactions.py")
        
    st.markdown("<div id='earnings-section'></div><br><hr style='border-color: var(--border-color);'><br>", unsafe_allow_html=True)
    lang = st.session_state.get("lang", "zh")
    show_earnings_calendar(lang, is_empty=True)

if not holdings.empty and not is_loading_prices:
    lang = st.session_state.get("lang", "zh")
    

    
    held_symbols = holdings[holdings["total_shares"] > 0]["symbol"].tolist()
    
    # === 0. 績效走勢 (Performance Curve) ===
    st.markdown("<h3 style='margin-left: 8px; margin-bottom: 20px; font-size: 22px; font-weight: bold; color: #ffffff;'>📈 績效走勢 (Performance)</h3>", unsafe_allow_html=True)
    with st.spinner("計算歷史績效中..." if lang == "zh" else "Đang tính toán hiệu suất..."):
        hist_df = compute_historical_equity(days=180)
        if hist_df is not None and not hist_df.empty:
            import plotly.graph_objects as go
            fig = go.Figure()
            
            # 你的投資組合
            fig.add_trace(go.Scatter(
                x=hist_df['Date'], 
                y=hist_df['Portfolio_Base100'],
                mode='lines',
                name='投資組合 (My Portfolio)',
                line=dict(color='#00F0FF', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 240, 255, 0.1)',
                hovertemplate='%{y:.2f}'
            ))
            
            # 大盤指標
            fig.add_trace(go.Scatter(
                x=hist_df['Date'], 
                y=hist_df['VNINDEX_Base100'],
                mode='lines',
                name='越南大盤 (VN-Index)',
                line=dict(color='#FF2A85', width=2, dash='dot'),
                hovertemplate='%{y:.2f}'
            ))
            
            fig.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color='white')
                ),
                xaxis=dict(
                    showgrid=False, 
                    color='#cbd5e1',
                    tickformat='%m-%d'
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(255,255,255,0.05)', 
                    color='#cbd5e1',
                    title='Base 100'
                ),
                hovermode="x unified"
            )
            
            st.markdown("<div style='background: var(--bg-card); padding: 15px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);'>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("尚無足夠的歷史資料來繪製走勢圖。" if lang == "zh" else "Chưa đủ dữ liệu lịch sử để vẽ biểu đồ.")
            
    st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)
    
    # 1. 財報預告時間表 (Earnings Calendar Section)
    show_earnings_calendar(lang, is_empty=False)
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # 2. 🔍 手動新增其他追蹤股票 (Watchlist Manager - placed below calendar)
    render_watchlist_manager(lang, held_symbols)
    
    st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)
    
    # 3. 今日最新持股動態 (News Section)
    news_title = "今日最新持股動態" if lang == "zh" else "Tin tức mới nhất về cổ phiếu"
    st.markdown(f"<h3 style='margin-left: 8px; margin-bottom: 20px; font-size: 22px; font-weight: bold; color: #ffffff;'>📰 {news_title}</h3>", unsafe_allow_html=True)
    
    from news_utils import fetch_all_news_parallel
    
    with st.spinner("Fetching latest news..." if lang == "zh" else "Đang tải tin tức..."):
        all_news = fetch_all_news_parallel(held_symbols, lang=lang, limit=2)
        
    if not all_news:
        search_txt = "前往 CafeF 搜尋" if lang == "zh" else "Tìm trên CafeF"
        st.html(clean_html(f"""
        <div class="empty-state" style="padding: 30px; border: 1px dashed var(--border-color); text-align: center; border-radius: 12px; background: var(--bg-card);">
            <div style="font-size: 36px; margin-bottom: 10px;">📰</div>
            <div style="font-size: 15px; color: #cbd5e1; line-height: 1.5; margin-bottom: 18px;">
                {"今日無相關新聞" if lang == "zh" else "Không có tin tức nào hôm nay"}
            </div>
            <a href="https://s.cafef.vn/tim-kiem.chn" target="_blank" style="color: #00F0FF; text-decoration: none; font-size: 13.5px; font-weight: bold; background: rgba(0, 240, 255, 0.08); padding: 8px 20px; border-radius: 8px; border: 1px solid rgba(0, 240, 255, 0.25); display: inline-block;">
                🔍 {search_txt}
            </a>
        </div>
        """))
    else:
        # Sort news by parsing the RFC 2822 date string to ensure chronological order
        import email.utils
        from datetime import datetime, timezone
        def _parse_pubdate(dstr):
            try:
                return email.utils.parsedate_to_datetime(dstr)
            except:
                return datetime.now(timezone.utc)
        all_news.sort(key=lambda x: _parse_pubdate(x.get("pubDate", "")), reverse=True)
        
        with st.container(height=520):
            for item in all_news:
                is_held = item['symbol'] in held_symbols
                badge_class = "news-badge held" if is_held else "news-badge"
                favicon_url = get_favicon_url(item['symbol'])
                
                news_card_html = f"""
                <div class="news-card">
                    <div class="{badge_class}">
                        <img src="{favicon_url}" style="width: 15px; height: 15px; border-radius: 3px;">
                        <span>{item['symbol']}</span>
                    </div>
                    <div style="flex-grow: 1;">
                        <a href="{item['link']}" target="_blank" style="color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; display: block; margin-bottom: 6px; line-height: 1.4; transition: all 0.2s;" onmouseover="this.style.color='#00F0FF'" onmouseout="this.style.color='#ffffff'">
                            {item['title']}
                        </a>
                        <div style="font-size: 12px; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
                            <span>🕒 {item['pubDate'][:16]}</span>
                        </div>
                    </div>
                </div>
                """
                st.html(clean_html(news_card_html))
