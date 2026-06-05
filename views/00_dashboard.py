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
    padding: 1px 3px;
    font-size: 9px;
    font-weight: bold;
    text-align: center;
    margin-top: 2px;
    display: inline-block;
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

    def render_grid_html(title_str, grid_data, events_map):
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
                        for ev in events_map[day]:
                            color_bg = ev["color"]
                            prefix = "⭐ " if ev.get("is_holding") else ""
                            html.append(f'<span class="calendar-stock-tag" style="background: {color_bg}22; border: 1px solid {color_bg}88; color: {color_bg};">{prefix}{ev["symbol"]}</span>')
                    html.append('</div>')
                    
        html.append('</div></div>')
        return "".join(html)

    # Setup the 4 Quarter tabs
    tab_q1, tab_q2, tab_q3, tab_q4 = st.tabs([
        "🌸 Q1 財報季 (4月)" if lang == "zh" else "🌸 Mùa BCTC Q1 (T4)",
        "🔥 Q2 財報季 (7月)" if lang == "zh" else "🔥 Mùa BCTC Q2 (T7)",
        "🍁 Q3 財報季 (10月)" if lang == "zh" else "🍁 Mùa BCTC Q3 (T10)",
        "❄️ Q4/全年 財報季 (1月)" if lang == "zh" else "❄️ Mùa BCTC Q4/Cả năm (T1)"
    ])

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

    # Helper function to render a single tab's content
    def render_tab_content(q_key, grid_data, title_str, selectbox_key):
        q_events = get_quarter_events(q_key, held_symbols)
        st.markdown(render_grid_html(title_str, grid_data, q_events), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        # Build select list of symbols for this quarter
        quarter_symbols = []
        for d, evs in q_events.items():
            for ev in evs:
                quarter_symbols.append(ev["symbol"])
        quarter_symbols = sorted(list(set(quarter_symbols)))
        
        if not quarter_symbols:
            st.write("本季無相關財報資料" if lang == "zh" else "Không có dữ liệu BCTC cho quý này")
            return

        col_sel, col_det = st.columns([1.5, 2.5])
        with col_sel:
            selected_sym = st.selectbox(
                "🔍 選擇標的查看財報詳情" if lang == "zh" else "🔍 Chọn mã xem chi tiết BCTC",
                options=quarter_symbols,
                key=selectbox_key
            )
            
        # Check if custom detail or base detail
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
            
            info = {
                "type": "您的持股" if lang == "zh" else "Cổ phiếu sở hữu",
                "expected_growth": "密切追蹤" if lang == "zh" else "Theo dõi sát",
                "desc": f"這是您的投資組合持股。{holding_info_str} 預計於該日附近公布財報，請密切注意損益變化與公司公告。" if lang == "zh" else f"Đây là cổ phiếu trong danh mục của bạn. {holding_info_str} BCTC dự kiến công bố quanh ngày này, hãy theo dõi sát sao."
            }
            
        st_color = "#10B981" if selected_sym in held_symbols else "#00F0FF"
        badge_html = f'<span style="font-size:16px; font-weight:bold; color:{st_color};">{"⭐ " if selected_sym in held_symbols else ""}{selected_sym}</span>'
        
        with col_det:
            st.markdown(f"""
            <div class="cathay-card" style="background: var(--bg-card); padding: 12px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                    {badge_html}
                    <span style="font-size:11px; color:#cbd5e1; background:rgba(255,255,255,0.05); padding:1px 6px; border-radius:10px;">{info['type']}</span>
                </div>
                <div style="margin: 4px 0; display:flex; gap: 6px; flex-wrap: wrap;">
                    <span style="background:rgba(236,72,153,0.1); border:1px solid rgba(236,72,153,0.3); color:#f472b6; padding:1px 4px; border-radius:4px; font-size:10px; font-weight:bold;">
                        📅 預計發布: {date_str}
                    </span>
                    <span style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399; padding:1px 4px; border-radius:4px; font-size:10px; font-weight:bold;">
                        🚀 預期成長: {info['expected_growth']}
                    </span>
                </div>
                <div style="font-size:12px; color:#cbd5e1; line-height:1.4; margin-top:4px;">
                    {info['desc']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_q1:
        title = "📅 2026年4月份 - 第一季 (Q1) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q1 - Tháng 04/2026"
        render_tab_content("Q1", grid_q1, title, f"earnings_q1_{'empty' if is_empty else 'full'}")
        
    with tab_q2:
        title = "📅 2026年7月份 - 第二季 (Q2) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q2 - Tháng 07/2026"
        render_tab_content("Q2", grid_q2, title, f"earnings_q2_{'empty' if is_empty else 'full'}")
        
    with tab_q3:
        title = "📅 2026年10月份 - 第三季 (Q3) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q3 - Tháng 10/2026"
        render_tab_content("Q3", grid_q3, title, f"earnings_q3_{'empty' if is_empty else 'full'}")
        
    with tab_q4:
        title = "📅 2027年1月份 - 第四季及全年 (Q4) 財報時間表" if lang == "zh" else "📅 Lịch công bố BCTC Q4/Cả năm - Tháng 01/2027"
        render_tab_content("Q4", grid_q4, title, f"earnings_q4_{'empty' if is_empty else 'full'}")


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
        st.markdown(f"""
        <div class="cathay-card" style="background: var(--bg-card); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 20px; text-align: center;">
            <span style="font-size: 15px; color: #94a3b8; display: block; margin-bottom: 10px;">
                {"今日無相關新聞" if lang == "zh" else "Không có tin tức nào hôm nay"}
            </span>
            <a href="https://s.cafef.vn/tim-kiem.chn" target="_blank" style="color: #00F0FF; text-decoration: none; font-size: 15px; font-weight: bold; background: rgba(0, 240, 255, 0.1); padding: 8px 16px; border-radius: 20px;">
                🔍 {search_txt}
            </a>
        </div>
        """, unsafe_allow_html=True)
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
                st.markdown(f"""
                <div class="cathay-card" style="background: var(--bg-card); padding: 12px 14px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); margin-bottom: 10px; display: flex; align-items: flex-start; gap: 12px;">
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
                </div>
                """, unsafe_allow_html=True)
                
    st.markdown("<br><hr style='border-color: var(--border-color); opacity: 0.5;'><br>", unsafe_allow_html=True)
    
    # 2. 財報預告時間表 (Earnings Calendar Section)
    show_earnings_calendar(lang, is_empty=False)
