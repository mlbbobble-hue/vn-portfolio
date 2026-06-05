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
from portfolio import compute_portfolio_with_prices, get_total_realized_pl, compute_received_dividends
from db_router import get_price_cache
from config import PRICE_REFRESH_SECONDS

st.markdown("""
<style>
/* 針對本頁面的微調 */
.app-title-small { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; display:block; }
.empty-state { text-align: center; padding: 40px 20px; background: var(--bg-card); border-radius: 12px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; color: var(--text-secondary); }
.empty-text { color: var(--text-secondary); font-size: 16px; margin-bottom: 24px; }
</style>
""", unsafe_allow_html=True)


if not check_auth():
    st.stop()

# 獲取資料



holdings = compute_portfolio_with_prices()

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
    border-radius: 4px;
    padding: 2px 5px;
    font-size: 9px;
    font-weight: bold;
    text-align: center;
    margin-top: 2px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
    text-decoration: none !important;
}
.calendar-stock-tag:hover {
    transform: scale(1.05);
}
</style>""", unsafe_allow_html=True)

    # Fetch held symbols
    held_symbols = []
    if not is_empty:
        try:
            held_symbols = holdings[holdings["total_shares"] > 0]["symbol"].tolist()
        except:
            pass

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

    def get_quarter_events(q_key, held_list):
        events_map = {}
        max_days = {"Q1": 30, "Q2": 31, "Q3": 30, "Q4": 29}
        limit_day = max_days.get(q_key, 30)
        
        for day, evs in base_events.items():
            target_day = day if day <= limit_day else limit_day
            if target_day not in events_map:
                events_map[target_day] = []
            for ev in evs:
                is_held = ev["symbol"] in held_list
                events_map[target_day].append({
                    "symbol": ev["symbol"],
                    "color": "#10B981" if is_held else ev["color"],
                    "is_holding": is_held
                })
                
        for sym in held_list:
            already_added = False
            for d, evs in events_map.items():
                if any(e["symbol"] == sym for e in evs):
                    already_added = True
                    break
            if not already_added:
                d = get_symbol_day(sym, q_key)
                if d not in events_map:
                    events_map[d] = []
                events_map[d].append({
                    "symbol": sym,
                    "color": "#10B981",
                    "is_holding": True
                })
        return events_map

    def render_grid_html(title_str, grid_data, events_map, q_key):
        html = []
        html.append('<div class="calendar-container">')
        html.append(f'<div class="calendar-title">{title_str}</div>')
        html.append('<div class="calendar-grid">')
        
        for h in headers:
            html.append(f'<div class="calendar-header-cell">{h}</div>')
            
        for week in grid_data:
            for day in week:
                if day is None:
                    html.append('<div class="calendar-empty-cell"></div>')
                else:
                    html.append('<div class="calendar-day-cell">')
                    html.append(f'<div class="calendar-day-num">{day:02d}</div>')
                    if day in events_map:
                        html.append('<div style="display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px;">')
                        for ev in events_map[day]:
                            color_bg = ev["color"]
                            prefix = "⭐ " if ev.get("is_holding") else ""
                            tooltip = f"{prefix}{ev['symbol']}"
                            img_style = f"width: 24px; height: 24px; border-radius: 6px; border: 1px solid var(--border-color); padding: 1px; background: rgba(255,255,255,0.08); transition: all 0.15s ease-in-out; vertical-align: middle; cursor: pointer;"
                            span_id = f"fallback_{q_key}_{day}_{ev['symbol']}"
                            span_style = f"display: none; font-size: 9px; font-weight: bold; color: {color_bg}; background: {color_bg}22; border: 1px solid {color_bg}88; padding: 1px 3px; border-radius: 4px;"
                            
                            html.append(f'<a href="?select_stock={ev["symbol"]}&q_tab={q_key}" target="_parent" style="text-decoration: none;" title="{tooltip}">')
                            html.append(f'<img src="{get_favicon_url(ev["symbol"])}" style="{img_style}" onmouseover="this.style.transform=\'scale(1.15)\'; this.style.borderColor=\'#00F0FF\';" onmouseout="this.style.transform=\'scale(1)\'; this.style.borderColor=\'var(--border-color)\';" onerror="this.style.display=\'none\'; document.getElementById(\'{span_id}\').style.display=\'inline-block\';">')
                            html.append(f'<span id="{span_id}" style="{span_style}">{prefix}{ev["symbol"]}</span>')
                            html.append('</a>')
                        html.append('</div>')
                    html.append('</div>')
                    
        html.append('</div></div>')
        return "".join(html)

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
        "FRT": {"type": "醫藥零售" if lang == "zh" else "Bán lẻ dược phẩm", "actual_growth": "YoY +300%+", "desc": "Q1 營收 9,040 億 VND，淨利 61 億 VND。龍洲藥局連鎖店數增至 1,600 家，單店坪效維持高檔，正式進入獲利貢獻期。" if lang == "zh" else "LNST Q1 đạt 61 tỷ VND. Chuỗi nhà thuốc Long Châu tiếp tục là động lực tăng trưởng cốt lõi với doanh thu bùng nổ."}
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
        "FRT": {"type": "醫藥零售" if lang == "zh" else "Bán lẻ dược phẩm", "expected_growth": "YoY +90%+", "desc": "龍洲藥局快速擴張並進入收割期。連鎖藥局獲利成長顯著，帶動 FRT 營收大增。" if lang == "zh" else "Chuỗi nhà thuốc Long Châu tiếp tục bứt phá mạnh mẽ làm động lực tăng trưởng chính."}
    }

    # Render selected quarter content
    q_events = get_quarter_events(q_key, held_symbols)
    
    grid_map = {
        "Q1": (grid_q1, "📅 2026年4月份 - 第一季 (Q1) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q1 - Tháng 04/2026"),
        "Q2": (grid_q2, "📅 2026年7月份 - 第二季 (Q2) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q2 - Tháng 07/2026"),
        "Q3": (grid_q3, "📅 2026年10月份 - 第三季 (Q3) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q3 - Tháng 10/2026"),
        "Q4": (grid_q4, "📅 2027年1月份 - 第四季及全年 (Q4) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q4/Cả năm - Tháng 01/2027")
    }
    
    selected_grid, title_str = grid_map.get(q_key, (grid_q2, ""))
    
    st.markdown(render_grid_html(title_str, selected_grid, q_events, q_key), unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    
    # Build select list of symbols for this quarter
    quarter_symbols = []
    for d, evs in q_events.items():
        for ev in evs:
            quarter_symbols.append(ev["symbol"])
    quarter_symbols = sorted(list(set(quarter_symbols)))
    
    if quarter_symbols:
        col_sel, col_det = st.columns([1.5, 2.5])
        
        # Calculate select index if query param matches
        default_sel_idx = 0
        if selected_stock_param in quarter_symbols:
            default_sel_idx = quarter_symbols.index(selected_stock_param)
            
        with col_sel:
            selected_sym = st.selectbox(
                "🔍 選擇標的查看財報詳情" if lang == "zh" else "🔍 Chọn mã xem chi tiết BCTC",
                options=quarter_symbols,
                index=default_sel_idx,
                key=f"earnings_select_box_{q_key}_{'empty' if is_empty else 'full'}"
            )
            
        # Check if custom detail or base detail
        if q_key == "Q1":
            info = details_q1.get(selected_sym, None)
        else:
            info = details_base.get(selected_sym, None)
            
        year_month = {"Q1": "2026-04", "Q2": "2026-07", "Q3": "2026-10", "Q4": "2027-01"}.get(q_key, "2026-07")
        
        # Determine actual day assigned
        assigned_day = 15
        for d, evs in q_events.items():
            if any(e["symbol"] == selected_sym for e in evs):
                assigned_day = d
                break
        date_str = f"{year_month}-{assigned_day:02d}"
        
        if info is None:
            # Generate custom dynamic detail for user holdings
            holding_info_str = ""
            if not holdings.empty and selected_sym in holdings["symbol"].values:
                row = holdings[holdings["symbol"] == selected_sym].iloc[0]
                shares = row["total_shares"]
                cost = row["total_cost"]
                unrealized = row["unrealized_pl"]
                holding_info_str = (
                    f"您的持股數: {shares:,.0f} 股，持有成本: {cost:,.0f} VND，未實現損益: {unrealized:+,.0f} VND。"
                    if lang == "zh" else
                    f"Số lượng sở hữu: {shares:,.0f} CP, Giá vốn: {cost:,.0f} VND, Lợi nhuận tạm tính: {unrealized:+,.0f} VND."
                )
            
            if q_key == "Q1":
                info = {
                    "type": "您的持股" if lang == "zh" else "Cổ phiếu sở hữu",
                    "growth_key": "已公布" if lang == "zh" else "Đã công bố",
                    "growth_val": "請查看明細" if lang == "zh" else "Xem chi tiết",
                    "desc": f"這是您的投資組合持股 {selected_sym}。Q1 財報已於該日附近公布。{holding_info_str} 建議前往交易明細或新聞專欄查看 Q1 損益與分紅發放決議。" if lang == "zh" else f"Đây là cổ phiếu {selected_sym} của bạn. BCTC Q1 đã được công bố. {holding_info_str} Vui lòng xem chi tiết giao dịch hoặc tin tức để biết thêm chi tiết."
                }
            else:
                info = {
                    "type": "您的持股" if lang == "zh" else "Cổ phiếu sở hữu",
                    "growth_key": "預期成長" if lang == "zh" else "Tăng trưởng dự kiến",
                    "growth_val": "密切追蹤" if lang == "zh" else "Theo dõi sát",
                    "desc": f"這是您的投資組合持股。{holding_info_str} 預計於該日附近公布財報，請密切注意損益變化與公司公告。" if lang == "zh" else f"Đây là cổ phiếu trong danh mục của bạn. {holding_info_str} BCTC dự kiến công bố quanh ngày này, hãy theo dõi sát sao."
                }
        else:
            if q_key == "Q1":
                info = {
                    "type": info["type"],
                    "growth_key": "淨利成長" if lang == "zh" else "Tăng trưởng LNST",
                    "growth_val": info["actual_growth"],
                    "desc": info["desc"]
                }
            else:
                info = {
                    "type": info["type"],
                    "growth_key": "預期成長" if lang == "zh" else "Tăng trưởng dự kiến",
                    "growth_val": info["expected_growth"],
                    "desc": info["desc"]
                }
            
        st_color = "#10B981" if selected_sym in held_symbols else "#00F0FF"
        badge_html = f'<span style="font-size:16px; font-weight:bold; color:{st_color};">{"⭐ " if selected_sym in held_symbols else ""}{selected_sym}</span>'
        
        # Render the card with dynamic labels
        date_label = "實際發布" if q_key == "Q1" else "預計發布"
        if lang != "zh":
            date_label = "Ngày công bố" if q_key == "Q1" else "Dự kiến công bố"
            
        with col_det:
            st.markdown(f"""<div class="cathay-card" style="background: var(--bg-card); padding: 12px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
{badge_html}
<span style="font-size:11px; color:#cbd5e1; background:rgba(255,255,255,0.05); padding:1px 6px; border-radius:10px;">{info['type']}</span>
</div>
<div style="margin: 4px 0; display:flex; gap: 6px; flex-wrap: wrap;">
<span style="background:rgba(236,72,153,0.1); border:1px solid rgba(236,72,153,0.3); color:#f472b6; padding:1px 4px; border-radius:4px; font-size:10px; font-weight:bold;">
📅 {date_label}: {date_str}
</span>
<span style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399; padding:1px 4px; border-radius:4px; font-size:10px; font-weight:bold;">
🚀 {info['growth_key']}: {info['growth_val']}
</span>
</div>
<div style="font-size:12px; color:#cbd5e1; line-height:1.4; margin-top:4px;">
{info['desc']}
</div>
</div>""", unsafe_allow_html=True)


if holdings.empty:
    st.markdown(f'''
    <div class="empty-state">
        <div class="empty-icon">🌱</div>
        <div class="empty-text">{t("portfolio_empty_desc")}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    if st.button(t("go_to_add_tx"), use_container_width=True):
        st.switch_page("views/02_transactions.py")
        
    st.markdown("<br><hr style='border-color: var(--border-color);'><br>", unsafe_allow_html=True)
    lang = st.session_state.get("lang", "zh")
    show_earnings_calendar(lang, is_empty=True)

if not holdings.empty and not is_loading_prices:
    st.markdown("<br>", unsafe_allow_html=True)
    lang = st.session_state.get("lang", "zh")
    
    # 1. 今日最新持股動態 (News Section)
    news_title = "今日最新持股動態" if lang == "zh" else "Tin tức mới nhất về cổ phiếu"
    st.markdown(f"<h4 style='margin-left: 8px; margin-bottom: 16px;'>{news_title}</h4>", unsafe_allow_html=True)
    
    from news_utils import fetch_all_news_parallel
    
    # Get all current holdings where total_shares > 0
    all_symbols = holdings[holdings["total_shares"] > 0]["symbol"].tolist()
    
    with st.spinner("Fetching latest news..." if lang == "zh" else "Đang tải tin tức..."):
        all_news = fetch_all_news_parallel(all_symbols, lang=lang, limit=2)
    
    if not all_news:
        search_txt = "前往 CafeF 搜尋" if lang == "zh" else "Tìm trên CafeF"
        st.markdown(f"""<div class="cathay-card" style="background: var(--bg-card); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 20px; text-align: center;">
<span style="font-size: 15px; color: #94a3b8; display: block; margin-bottom: 10px;">
{"今日無相關新聞" if lang == "zh" else "Không có tin tức nào hôm nay"}
</span>
<a href="https://s.cafef.vn/tim-kiem.chn" target="_blank" style="color: #00F0FF; text-decoration: none; font-size: 15px; font-weight: bold; background: rgba(0, 240, 255, 0.1); padding: 8px 16px; border-radius: 20px;">
🔍 {search_txt}
</a>
</div>""", unsafe_allow_html=True)
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
        
        with st.container(height=380):
            for item in all_news:
                st.markdown(f"""<div class="cathay-card" style="background: var(--bg-card); padding: 12px 14px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 10px; display: flex; align-items: flex-start; gap: 12px;">
<div style="background: rgba(37, 99, 235, 0.15); border: 1px solid rgba(37, 99, 235, 0.5); color: #60a5fa; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; min-width: 55px; text-align: center; flex-shrink: 0; align-self: flex-start; margin-top: 3px;">
{item['symbol']}
</div>
<div>
<a href="{item['link']}" target="_blank" style="color: #ffffff; text-decoration: none; font-weight: 500; font-size: 15px; display: block; margin-bottom: 6px; line-height: 1.4; transition: color 0.2s;" onmouseover="this.style.color='#00F0FF'" onmouseout="this.style.color='#ffffff'">
{item['title']}
</a>
<div style="font-size: 12px; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
<span>🕒 {item['pubDate'][:16]}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)
                
    st.markdown("<br><hr style='border-color: var(--border-color); opacity: 0.5;'><br>", unsafe_allow_html=True)
    
    # 2. 財報預告時間表 (Earnings Calendar Section)
    show_earnings_calendar(lang, is_empty=False)
