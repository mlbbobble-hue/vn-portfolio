"""頁面4：觀察清單（雙語 + db_router）"""
import streamlit as st
import pandas as pd
import textwrap
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (get_watchlist, upsert_watchlist, delete_watchlist,
                        save_notification_settings, load_notification_settings,
                        get_price_cache, upsert_price_cache)
from market_data import get_stock_price, get_moving_average
from alerts import test_notification, check_and_fire_alerts
from portfolio import get_estimated_yield, get_dividend_income_summary

RECOMMENDED_STOCKS_YIELD = [
    {"symbol": "VEA", "name_zh": "越南農業機械引擎", "name_vi": "Động cơ Việt Nam", "industry_zh": "汽車與機械製造", "industry_vi": "Sản xuất cơ khí", "metric_val": "12% ~ 14%", "desc_zh": "越股存股首選！持有本田(Honda)、豐田(Toyota)、福特(Ford)在越合資公司大筆股權，躺著收息。", "desc_vi": "Nắm giữ cổ phần lớn tại các liên doanh Honda, Toyota, Ford tại Việt Nam, dòng tiền cổ tức cực kỳ lớn."},
    {"symbol": "BMP", "name_zh": "平明塑膠", "name_vi": "Nhựa Bình Minh", "industry_zh": "工業建材", "industry_vi": "VLXD & Công nghiệp", "metric_val": "8% ~ 10%", "desc_zh": "越南塑膠管龍頭，財務極為健全且近乎無負債，手頭現金滿滿，分紅極高。", "desc_vi": "Doanh nghiệp nhựa xây dựng đầu ngành, tài chính lành mạnh, không nợ vay, trả cổ tức tiền mặt lớn."},
    {"symbol": "SCS", "name_zh": "西貢航空易貨服務", "name_vi": "Dịch vụ Hàng hóa Sài Gòn", "industry_zh": "航空物流", "industry_vi": "Logistics Hàng không", "metric_val": "7% ~ 9%", "desc_zh": "壟斷新山一機場的貨運裝卸服務，高淨利率、零負債，出口貿易增長直接受益者。", "desc_vi": "Độc quyền dịch vụ nhà ga hàng hóa tại sân bay Tân Sơn Nhất, biên lợi nhuận cao, không nợ vay."},
    {"symbol": "QNS", "name_zh": "廣義糖業", "name_vi": "Đường Quảng Ngãi", "industry_zh": "食品飲料", "industry_vi": "Thực phẩm & Đồ uống", "metric_val": "6% ~ 8%", "desc_zh": "旗下「Fami豆奶」是越南市佔第一品牌，業績非常穩定，現金配息大方且穩定。", "desc_vi": "Sở hữu thương hiệu sữa đậu nành Fami dẫn đầu thị phần, dòng tiền mặt kinh doanh dồi dào."},
    {"symbol": "DPM", "name_zh": "富美肥料", "name_vi": "Phân bón Hóa chất Dầu khí", "industry_zh": "農業化學", "industry_vi": "Hóa chất nông nghiệp", "metric_val": "7% ~ 9%", "desc_zh": "國營尿素肥料龍頭，手頭現金充沛，歷史配息紀錄極佳，唯有行業週期波動。", "desc_vi": "Doanh nghiệp phân đạm đầu ngành, lượng tiền mặt lớn, lịch sử trả cổ tức tiền mặt bền bỉ."},
    {"symbol": "DCM", "name_zh": "金甌肥料", "name_vi": "Phân bón Dầu khí Cà Mau", "industry_zh": "農業化學", "industry_vi": "Hóa chất nông nghiệp", "metric_val": "6% ~ 8%", "desc_zh": "與 DPM 並列的肥料雙雄，廠房折舊完畢後自由現金流大幅提升，配息能力優異。", "desc_vi": "Nhà máy hết khấu hao giúp dòng tiền tự do tăng mạnh, nâng cao năng lực chi trả cổ tức."},
    {"symbol": "DVP", "name_zh": "亭武港口", "name_vi": "Cảng Đình Vũ", "industry_zh": "港口物流", "industry_vi": "Cảng biển & Logistics", "metric_val": "8% ~ 10%", "desc_zh": "海防港區的重要港口，經營穩定、負債極低，歷史上一直維持高比例現金分紅。", "desc_vi": "Cảng biển lớn tại Hải Phòng, hoạt động ổn định, nợ vay thấp, lịch sử chia cổ tức cao."},
    {"symbol": "QTP", "name_zh": "廣寧熱電", "name_vi": "Nhiệt điện Quảng Ninh", "industry_zh": "電力公用事業", "industry_vi": "Điện & Năng lượng", "metric_val": "8% ~ 10%", "desc_zh": "隨著設備折舊完畢、債務清償，可分配現金大幅增加，是電力股中的高息明珠。", "desc_vi": "Hết khấu hao tài sản và trả xong nợ giúp dòng tiền tăng vọt, cổ tức tiền mặt ổn định."},
    {"symbol": "VNM", "name_zh": "越南牛奶 (Vinamilk)", "name_vi": "Vinamilk", "industry_zh": "食品飲料", "industry_vi": "Thực phẩm & Đồ uống", "metric_val": "5.5% ~ 6.5%", "desc_zh": "越南民生消費權值股，護城河極深，防禦型存股，每年配息極具規律性。", "desc_vi": "Cổ phiếu tiêu dùng đầu ngành, phòng thủ tốt, dòng tiền mạnh và chia cổ tức đều đặn hàng năm."},
    {"symbol": "SAB", "name_zh": "薩貝科啤酒", "name_vi": "Sabeco", "industry_zh": "食品飲料", "industry_vi": "Thực phẩm & Đồ uống", "metric_val": "6.0% ~ 7.0%", "desc_zh": "西貢啤酒母公司，市佔率極高。由泰國集團控股後，推動了高比例現金股息政策。", "desc_vi": "Sở hữu thương hiệu Bia Sài Gòn, tập đoàn ThaiBev nắm quyền chi phối duy trì cổ tức cao."}
]

RECOMMENDED_STOCKS_ROE = [
    {"symbol": "FPT", "name_zh": "FPT 科技集團", "name_vi": "Tập đoàn FPT", "industry_zh": "資訊軟體服務", "industry_vi": "Công nghệ thông tin", "metric_val": "25% ~ 28%", "desc_zh": "越南科技業霸主，軟體外包訂單強勁。高 ROE 代表資金運用效率極佳，股東報酬豐厚。", "desc_vi": "Tập đoàn công nghệ thông tin hàng đầu Việt Nam, tỷ suất sinh lời trên vốn (ROE) cực kỳ hiệu quả."},
    {"symbol": "SCS", "name_zh": "西貢航空易貨服務", "name_vi": "Dịch vụ Hàng hóa Sài Gòn", "industry_zh": "航空物流", "industry_vi": "Logistics Hàng không", "metric_val": "35% ~ 40%", "desc_zh": "獨家經營新山一機場航空貨運。幾乎無負債、高淨利率，股本回報率（ROE）冠絕越股。", "desc_vi": "Độc quyền dịch vụ hàng hóa sân bay Tân Sơn Nhất, biên lợi nhuận cao giúp duy trì ROE vượt trội."},
    {"symbol": "BMP", "name_zh": "平明塑膠", "name_vi": "Nhựa Bình Minh", "industry_zh": "工業建材", "industry_vi": "VLXD & Công nghiệp", "metric_val": "22% ~ 26%", "desc_zh": "越南塑膠管龍頭，財務極為穩健且無負債，高獲利回吐給股東，維持高 ROE 與高股息率。", "desc_vi": "Doanh nghiệp nhựa xây dựng đầu ngành, cơ cấu tài chính tối ưu mang lại ROE và cổ tức hấp dẫn."},
    {"symbol": "VCS", "name_zh": "Vicostone 石英石", "name_vi": "Vicostone", "industry_zh": "建材製造", "industry_vi": "Vật liệu xây dựng", "metric_val": "25% ~ 30%", "desc_zh": "人造石英石出口全球前三強。高毛利率、高技術與品牌壁壘，帶動卓越的 ROE 表現。", "desc_vi": "Top 3 thế giới về đá thạch anh nhân tạo, có vị thế xuất khẩu tốt duy trì ROE cao vững chắc."},
    {"symbol": "PNJ", "name_zh": "富潤珠寶", "name_vi": "Vàng bạc Đá quý Phú Nhuận", "industry_zh": "內需消費零售", "industry_vi": "Bán lẻ Trang sức", "metric_val": "20% ~ 22%", "desc_zh": "越南珠寶零售絕對龍頭，營運渠道廣泛，品牌護城河深厚，是消費板塊的高 ROE 代表。", "desc_vi": "Doanh nghiệp bán lẻ trang sức số 1 Việt Nam, khả năng sinh lời trên vốn chủ sở hữu rất ấn tượng."},
    {"symbol": "DGC", "name_zh": "德江化工", "name_vi": "Hóa chất Đức Giang", "industry_zh": "基礎化工", "industry_vi": "Hóa chất cơ bản", "metric_val": "30% ~ 35%", "desc_zh": "黃磷產能亞洲領先，是半導體製程的關鍵原料。技術與資源壟斷優勢帶來超高 ROE。", "desc_vi": "Nhà cung cấp phốt pho vàng hàng đầu Châu Á, biên lợi nhuận cao dẫn đến tỷ suất ROE vượt trội."},
    {"symbol": "TLG", "name_zh": "天龍文具", "name_vi": "Tập đoàn Thiên Long", "industry_zh": "文具製造", "industry_vi": "Sản xuất hàng tiêu dùng", "metric_val": "20% ~ 22%", "desc_zh": "越南文具絕對龍頭，內需剛性需求強，定價權高，營運效率優異，常年維持穩健的高 ROE。", "desc_vi": "Thống lĩnh thị trường văn phòng phẩm Việt Nam, biên lợi nhuận tốt giúp sinh lời vốn chủ rất đều."},
    {"symbol": "MSH", "name_zh": "May紅河紡織", "name_vi": "May Sông Hồng", "industry_zh": "紡織出口", "industry_vi": "Dệt may & Xuất khẩu", "metric_val": "21% ~ 24%", "desc_zh": "國際服飾代工大廠，產能與訂單穩定，固定資產周轉率快，股東權益報酬率優異。", "desc_vi": "Doanh nghiệp xuất khẩu dệt may quy mô lớn, có năng lực quản trị xuất sắc mang lại ROE tốt."}
]

RECOMMENDED_STOCKS_GROWTH = [
    {"symbol": "HPG", "name_zh": "和發集團", "name_vi": "Tập đoàn Hòa Phát", "industry_zh": "鋼鐵工業", "industry_vi": "Thép & Vật liệu", "metric_val": "YoY +120% ~ 150%+", "desc_zh": "越南鋼鐵巨人。受惠於公共建設復甦與榕橘二期建廠即將投產，淨利潤較去年低谷呈爆發式增長。", "desc_vi": "Tập đoàn thép lớn nhất Việt Nam, hưởng lợi từ đầu tư công và dự án Dung Quất 2 sắp đi vào hoạt động."},
    {"symbol": "FRT", "name_zh": "FPT 零售 (龍洲藥局)", "name_vi": "Bán lẻ FPT (Long Châu)", "industry_zh": "醫藥與零售", "industry_vi": "Dược phẩm & Bán lẻ", "metric_val": "YoY +80% ~ 100%+", "desc_zh": "旗下「龍洲藥局」為越南最大連鎖處方藥商，大舉擴張且單店營運轉盈，帶動集團獲利爆發性年增。", "desc_vi": "Chuỗi nhà thuốc Long Châu mở rộng mạnh mẽ và đóng góp lợi nhuận đột phá so với cùng kỳ năm ngoái."},
    {"symbol": "MWG", "name_zh": "移動世界", "name_vi": "Thế Giới Di Động", "industry_zh": "電子與內需零售", "industry_vi": "Bán lẻ Điện máy", "metric_val": "YoY +100% ~ 130%+", "desc_zh": "歷經渠道精簡與超市「百家綠」轉虧為盈，經營利潤自去年底大底翻揚，獲利倍增成長。", "desc_vi": "Tái cấu trúc chuỗi bán lẻ hiệu quả giúp Bách Hóa Xanh hòa vốn và có lãi, kéo lợi nhuận tập đoàn tăng vọt."},
    {"symbol": "FPT", "name_zh": "FPT 科技集團", "name_vi": "Tập đoàn FPT", "industry_zh": "資訊軟體服務", "industry_vi": "Công nghệ thông tin", "metric_val": "YoY +20% ~ 24%", "desc_zh": "軟體外包訂單常年飽滿，AI 與半導體封測佈局發酵。營收與淨利年增率持續穩定雙位數高成長。", "desc_vi": "Xuất khẩu phần mềm tăng trưởng hai con số đều đặn, doanh thu và lợi nhuận liên tục bứt phá."},
    {"symbol": "DGC", "name_zh": "德江化工", "name_vi": "Hóa chất Đức Giang", "industry_zh": "基礎化工", "industry_vi": "Hóa chất cơ bản", "metric_val": "YoY +30% ~ 45%+", "desc_zh": "受惠全球半導體製程復甦，電子級黃磷與磷酸產品價量齊揚，財報較去年同期明顯轉強增長。", "desc_vi": "Nhu cầu chất bán dẫn thế giới hồi phục làm giá phốt pho xuất khẩu tăng mạnh, giúp lợi nhuận YoY rất tốt."},
    {"symbol": "ACB", "name_zh": "亞洲商業銀行", "name_vi": "Ngân hàng ACB", "industry_zh": "金融銀行", "industry_vi": "Ngân hàng", "metric_val": "YoY +22% ~ 26%", "desc_zh": "風控最嚴格的民營銀行。信貸增長強勁且壞帳率低，利息與非利息淨利成長動能強大。", "desc_vi": "Ngân hàng TMCP có chất lượng tài sản tốt nhất, biên lợi nhuận giữ vững thúc đẩy tăng trưởng lợi nhuận."},
    {"symbol": "VHC", "name_zh": "永環水產", "name_vi": "Vĩnh Hoàn", "industry_zh": "海鮮出口", "industry_vi": "Thủy hải sản", "metric_val": "YoY +35% ~ 50%+", "desc_zh": "查魚出口女王。受惠於美國與歐洲市場庫存消耗完畢、訂單回溫，獲利同比表現大幅好轉。", "desc_vi": "Doanh nghiệp xuất khẩu cá tra lớn nhất sang Mỹ, đơn hàng phục hồi kéo theo lợi nhuận tăng mạnh."}
]

st.set_page_config(page_title=f"VN Portfolio | {t('watchlist_title')}", page_icon="🔔", layout="wide")
from theme import load_css
load_css()

if not check_auth():
    st.stop()

lang = st.session_state.get("lang", "zh")

st.markdown(textwrap.dedent(f"""
<div class="page-header">
    <h2>{t('watchlist_title')}</h2>
    <p>{t('watchlist_desc')}</p>
</div>"""), unsafe_allow_html=True)

# We simplified the tabs structure down to two: Recommendations & Watchlist, and Notification Settings
tab_main, tab_notify = st.tabs([
    t("tab_recommend_watchlist"), t("tab_notify")
])

with tab_main:
    wl = get_watchlist()
    price_cache = get_price_cache()
    price_map = {}
    if not price_cache.empty:
        price_map = price_cache.set_index("symbol")[["price","change_pct"]].to_dict("index")
    try:
        # Calculate dividends for both watchlist symbols and recommended symbols
        wl_symbols = wl["symbol"].tolist() if not wl.empty else []
        rec_symbols = list(set(
            [x["symbol"] for x in RECOMMENDED_STOCKS_YIELD] +
            [x["symbol"] for x in RECOMMENDED_STOCKS_ROE] +
            [x["symbol"] for x in RECOMMENDED_STOCKS_GROWTH]
        ))
        all_needed_symbols = list(set(wl_symbols + rec_symbols))
        div_summary = get_dividend_income_summary(all_needed_symbols)
        dps_map = {} if div_summary.empty else div_summary.set_index("symbol")["annual_dps"].to_dict()
    except Exception:
        dps_map = {}

    # ── Part A: 我的觀察清單 (My Watchlist) ─────────────────────────────────────────
    st.markdown("### 📊 我的觀察清單" if st.session_state.get("lang","zh")=="zh" else "### 📊 Danh sách theo dõi của tôi")
    
    if wl.empty:
        st.info(t("no_watchlist"))
    else:
        # --- MUJI Style Gauge Charts ---
        import plotly.graph_objects as go
        
        gauge_data = []
        for _, item in wl.iterrows():
            sym = item["symbol"]
            cur_price = price_map.get(sym,{}).get("price",0)
            target = item.get("target_price") or 0
            if target > 0 and cur_price > 0:
                dist_pct = (cur_price - target) / target * 100
                if dist_pct >= 0:
                    gauge_val = max(0, 100 - dist_pct)
                else:
                    gauge_val = 100
                gauge_data.append((sym, cur_price, target, gauge_val))
                
        if gauge_data:
            gauge_data.sort(key=lambda x: -x[3])
            top_gauges = gauge_data[:3]
            
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(len(top_gauges))
            
            for i, (sym, cur_price, target, g_val) in enumerate(top_gauges):
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = g_val,
                    number = {'suffix': "%", 'font': {'size': 24, 'color': '#FFFFFF'}},
                    title = {'text': f"<b>{sym}</b><br><span style='font-size:0.8em;color:#D8B4E2'>Target: {target:,.0f}</span>", 'font': {'size': 16, 'color': '#FFFFFF'}},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickwidth': 0, 'tickcolor': "rgba(255,255,255,0.05)", 'visible': False},
                        'bar': {'color': "#FF2A85" if g_val >= 90 else "#9D4EDD"},
                        'bgcolor': "#09090B",
                        'borderwidth': 0,
                        'shape': "angular"
                    }
                ))
                fig_gauge.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=30, b=10, l=10, r=10),
                    height=200
                )
                with cols[i]:
                    st.markdown("<div class='cathay-card' style='background: var(--bg-card); padding: 10px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); text-align:center;'>", unsafe_allow_html=True)
                    st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
                    st.markdown(f"<div style='font-size:14px;color:#D8B4E2;'>目前市價: {cur_price:,.0f}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
        wl_items = []
        for _, item in wl.iterrows():
            sym = item["symbol"]
            cur_price = price_map.get(sym, {}).get("price", 0)
            change = price_map.get(sym, {}).get("change_pct", 0)
            target = item.get("target_price") or 0
            enabled = bool(item.get("alert_enabled", 1))
            
            # Distance calculations
            dp = 999999.0
            dist_str = ""
            dist_color = "#D8B4E2"
            if target > 0 and cur_price > 0:
                dp = (cur_price - target) / target * 100
                dist_str = t("dist_to_target", pct=dp)
                dist_color = "#FF2A85" if dp <= 2 else "#9D4EDD" if dp <= 10 else "#D8B4E2"
                
            # Yield calculations
            annual_dps = dps_map.get(sym, 0)
            est_yield = 0.0
            ey_str = ""
            if annual_dps > 0 and cur_price > 0:
                est_yield = (annual_dps / cur_price) * 100
                ey_str = f"{t('est_yield_label', y=est_yield)}"
                
            price_str = f"{cur_price:,.0f} {t('vnd')}" if cur_price > 0 else "─"
            cc = "#FF2A85" if change > 0 else "#FF007F" if change < 0 else "#D8B4E2"
            cs = "▲" if change > 0 else "▼" if change < 0 else "─"
            
            badges = []
            if target > 0:
                badges.append(t("target_price_label", p=target))
            if item.get("ma60_alert"):
                badges.append(t("ma60_alert"))
            thresh = item.get("yield_threshold")
            if thresh:
                badges.append(t("yield_threshold", pct=thresh * 100))
                
            badge_str = "　".join(badges) if badges else t("no_alert")
            
            wl_items.append({
                "item": item,
                "symbol": sym,
                "cur_price": cur_price,
                "change": change,
                "target": target,
                "enabled": enabled,
                "dist_pct": dp,
                "dist_str": dist_str,
                "dist_color": dist_color,
                "est_yield": est_yield,
                "ey_str": ey_str,
                "price_str": price_str,
                "cc": cc,
                "cs": cs,
                "badge_str": badge_str
            })
            
        # Add sorting selectbox
        sort_by_label_yield = "預估殖利率 (由高到低)" if lang == "zh" else "Tỷ suất cổ tức (Cao -> Thấp)"
        sort_by_label_dist = "距離目標價 (由近到遠)" if lang == "zh" else "Khoảng cách mục tiêu (Gần -> Xa)"
        sort_by_label_alpha = "股票代號 (字母排序)" if lang == "zh" else "Mã CK (A -> Z)"
        
        sort_options = {
            sort_by_label_yield: lambda x: -x["est_yield"],
            sort_by_label_dist: lambda x: x["dist_pct"],
            sort_by_label_alpha: lambda x: x["symbol"],
        }
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_title, col_sort = st.columns([2, 1])
        with col_title:
            st.subheader(t("watching_count", n=len(wl)))
        with col_sort:
            selected_sort = st.selectbox(
                "排序方式" if lang == "zh" else "Sắp xếp theo",
                options=list(sort_options.keys()),
                key="wl_sort_by"
            )
            
        # Sort items
        wl_items.sort(key=sort_options[selected_sort])
        
        st.markdown("<br>", unsafe_allow_html=True)
        for w in wl_items:
            # Highlight high yield (>= 5% in green)
            yield_badge = ""
            if w["est_yield"] > 0:
                bg_color = "rgba(16, 185, 129, 0.15)" if w["est_yield"] >= 5.0 else "rgba(255, 255, 255, 0.05)"
                border_color = "rgba(16, 185, 129, 0.4)" if w["est_yield"] >= 5.0 else "rgba(255, 255, 255, 0.1)"
                text_color = "#34d399" if w["est_yield"] >= 5.0 else "#cbd5e1"
                
                # Create a small high yield tag
                yield_badge = f"""
                <span style="background: {bg_color}; border: 1px solid {border_color}; color: {text_color}; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-left: 10px; display: inline-block; vertical-align: middle;">
                    💎 {w['ey_str']}
                </span>
                """
                
            st.markdown(textwrap.dedent(f"""\
            <div class="cathay-card" style="padding:14px 18px;margin:6px 0; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);">
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        {"🟢" if w['enabled'] else "⚫"} <b style='color:var(--text-primary);font-size:1.05rem;vertical-align:middle;'>{w['symbol']}</b>
                        {yield_badge}
                        <span style='color:var(--text-secondary);margin-left:12px;vertical-align:middle;'>{w['price_str']}</span>
                        <span style='color:{w['cc']};margin-left:8px;vertical-align:middle;'>{w['cs']} {abs(w['change']):.2f}%</span>
                    </div>
                    <div style='color:{w['dist_color']};font-size:.9rem;'>{w['dist_str']}</div>
                </div>
                <div style='color:#64748b;font-size:.82rem;margin-top:6px;'>{w['badge_str']}</div>
            </div>"""), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t("update_wl_price"), use_container_width=True):
                with st.spinner(t("updating")):
                    from market_data import get_multiple_prices
                    prices_df = get_multiple_prices(all_needed_symbols)
                    for _, p in prices_df.iterrows():
                        upsert_price_cache(p["symbol"], p["price"], p["change_pct"], p.get("volume", 0))
                st.success(t("updated_count", n=len(prices_df)))
                st.rerun()
        with c2:
            if st.button(t("check_alerts"), use_container_width=True):
                fired = check_and_fire_alerts()
                if fired:
                    for f in fired:
                        st.warning(t("alert_fired", sym=f["symbol"], p=f["price"]))
                else:
                    st.success(t("no_alert_fired"))

    st.markdown("<br>", unsafe_allow_html=True)
    # Collapsible setting options
    c_add, c_del = st.columns(2)
    with c_add:
        with st.expander(t("add_watch_title"), expanded=False):
            st.markdown('<div class="card" style="padding: 10px; border: none; background: transparent;">', unsafe_allow_html=True)
            w_sym    = st.text_input(t("symbol"), key="w_sym").upper()
            w_target = st.number_input(t("target_price_input"), min_value=0, step=1000, value=0, key="w_target")
            w_ma60   = st.toggle(t("ma60_toggle"), key="w_ma60")
            w_yield  = st.number_input(t("yield_input"), min_value=0.0, max_value=30.0, step=0.5, value=0.0, key="w_yield")
            w_en     = st.toggle(t("enable_alert"), value=True, key="w_en")
            w_note   = st.text_input(t("note"), key="w_note")
            if st.button(t("add_watch_btn"), use_container_width=True):
                if not w_sym:
                    st.error(t("enter_symbol"))
                else:
                    upsert_watchlist(symbol=w_sym, target_price=w_target if w_target>0 else None,
                                     ma60_alert=1 if w_ma60 else 0,
                                     yield_threshold=w_yield/100 if w_yield>0 else None,
                                     alert_enabled=1 if w_en else 0, note=w_note)
                    st.success(t("add_watch_ok", sym=w_sym))
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander(t("alert_conditions"), expanded=False):
                st.markdown(f"""
                | {t('warning')} | Trigger | Use case |
                |---|---|---|
                | 🎯 **{t('target_price')}** | Price ≤ target | Buy on dip |
                | 📊 **MA60** | Price within ±2% of MA60 | Mean reversion |
                | 💰 **{t('yield_threshold')}** | Est. yield ≥ threshold | High yield entry |
                """)
    with c_del:
        with st.expander(t("remove_watch"), expanded=False):
            st.markdown('<div class="card" style="padding: 10px; border: none; background: transparent;">', unsafe_allow_html=True)
            del_sym = st.selectbox(t("remove_watch"), [""] + (wl["symbol"].tolist() if not wl.empty else []))
            if del_sym and st.button(t("remove_btn", sym=del_sym), use_container_width=True):
                delete_watchlist(del_sym)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Part B: 系統精選投資標的建議 (System Recommendations) ─────────────────────────────────────────
    st.divider()
    st.subheader("💡 投資標的建議" if lang == "zh" else "💡 Gợi ý đầu tư tiềm năng")
    st.markdown(
        "💡 系統精選越南股市中，**高殖利率存股、高 ROE 績優股與財報強勁增長**的優質標的。您可以選擇不同類別，並直接點擊「➕ 加入觀察」將其新增至您的追蹤清單。"
        if lang == "zh" else
        "💡 Danh sách cổ phiếu chi trả cổ tức cao, ROE vượt trội hoặc tăng trưởng lợi nhuận mạnh mẽ được hệ sinh thái đề xuất. Bạn có thể nhấn nút để thêm nhanh vào danh sách theo dõi."
    )
    
    # Select recommendation category
    recommend_type = st.selectbox(
        t("label_recommend_type"),
        options=["yield", "roe", "growth"],
        format_func=lambda x: {
            "yield": t("recommend_high_yield"),
            "roe": t("recommend_high_roe"),
            "growth": t("recommend_high_growth")
        }[x],
        key="recommend_category"
    )
    
    if recommend_type == "yield":
        rec_stocks = RECOMMENDED_STOCKS_YIELD
        metric_label = t("metric_high_yield")
    elif recommend_type == "roe":
        rec_stocks = RECOMMENDED_STOCKS_ROE
        metric_label = t("metric_high_roe")
    else:
        rec_stocks = RECOMMENDED_STOCKS_GROWTH
        metric_label = t("metric_high_growth")
        
    # Check what symbols are currently in the user's watchlist
    existing_watch_symbols = wl["symbol"].tolist() if not wl.empty else []
    
    # Render in a 2-column grid
    st.markdown("<br>", unsafe_allow_html=True)
    rec_col1, rec_col2 = st.columns(2)
    
    for idx, item in enumerate(rec_stocks):
        sym = item["symbol"]
        name = item["name_zh"] if lang == "zh" else item["name_vi"]
        industry = item["industry_zh"] if lang == "zh" else item["industry_vi"]
        desc = item["desc_zh"] if lang == "zh" else item["desc_vi"]
        metric_val = item["metric_val"]
        
        # Get live status from cache if available
        cur_price = price_map.get(sym, {}).get("price", 0)
        annual_dps = dps_map.get(sym, 0)
        
        live_yield_str = ""
        live_price_str = ""
        if cur_price > 0:
            live_price_str = f"💵 目前市價: {cur_price:,.0f} VND" if lang == "zh" else f"💵 Giá HT: {cur_price:,.0f} VNĐ"
            if annual_dps > 0:
                live_yield = (annual_dps / cur_price) * 100
                live_yield_str = f"✨ 即時殖利率: {live_yield:.2f}%" if lang == "zh" else f"✨ Tỷ suất HT: {live_yield:.2f}%"
                
        target_col = rec_col1 if idx % 2 == 0 else rec_col2
        
        with target_col:
            # Render a beautiful premium card - left-aligned to completely avoid markdown parsing issues
            card_html = f"""<div class="cathay-card" style="padding:16px; margin:8px 0; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); min-height: 230px; display: flex; flex-direction: column; justify-content: space-between;">
<div>
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:1.2rem; font-weight:bold; color:#00F0FF; vertical-align:middle;">{sym}</span>
<span style="font-size:0.8rem; color:#94a3b8; background:rgba(255,255,255,0.05); padding:2px 8px; border-radius:12px; vertical-align:middle;">{industry}</span>
</div>
<div style="font-size:0.95rem; font-weight:600; color:#ffffff; margin-top:4px;">{name}</div>
<div style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
<span style="background:rgba(236,72,153,0.1); border:1px solid rgba(236,72,153,0.3); color:#f472b6; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:bold;">
{metric_label}: {metric_val}
</span>
{f'<span style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:bold;">{live_yield_str}</span>' if live_yield_str else ""}
{f'<span style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#cbd5e1; padding:2px 6px; border-radius:4px; font-size:11px;">{live_price_str}</span>' if live_price_str else ""}
</div>
<div style="font-size:0.85rem; color:#cbd5e1; margin-top:12px; line-height:1.4;">
{desc}
</div>
</div>
</div>"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Action button
            is_added = sym in existing_watch_symbols
            if is_added:
                st.button(t("already_added"), key=f"rec_add_btn_{sym}", disabled=True, use_container_width=True)
            else:
                if st.button(t("add_to_watchlist"), key=f"rec_add_btn_{sym}", type="primary", use_container_width=True):
                    # Add with default values
                    upsert_watchlist(symbol=sym, alert_enabled=1, note="標的建議")
                    st.success(f"✅已將 {sym} 加入您的觀察清單！" if lang == "zh" else f"✅Đã thêm {sym} vào danh sách theo dõi!")
                    st.rerun()
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

# ── Tab 3: 通知 ─────────────────────────────────────────────
with tab_notify:
    st.subheader(t("notify_title"))
    settings = load_notification_settings()
    with st.expander(t("tg_setup_title"), expanded=False):
        st.markdown("1. Tìm @BotFather → /newbot → copy **BOT_TOKEN**\n2. Start Bot của bạn\n3. Truy cập `https://api.telegram.org/bot<TOKEN>/getUpdates` → copy **chat_id**" if st.session_state.get("lang","zh")=="vi" else
                    "1. 在 Telegram 搜尋 @BotFather → 發送 /newbot → 取得 **BOT_TOKEN**\n2. 開啟你的 Bot 點 Start\n3. 前往 `https://api.telegram.org/bot<TOKEN>/getUpdates` → 取得 **chat_id**")
    with st.expander(t("line_setup_title"), expanded=False):
        st.markdown("Truy cập https://notify-bot.line.me/my/ → Generate token → copy token" if st.session_state.get("lang","zh")=="vi" else
                    "前往 https://notify-bot.line.me/my/ → 點擊「Generate token」→ 複製 Token")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(t("tg_settings"))
    tg_token   = st.text_input(t("tg_bot_token"), value=settings.get("telegram_token",""), type="password", key="tg_tok")
    tg_chat_id = st.text_input(t("tg_chat_id"),   value=settings.get("telegram_chat_id",""), key="tg_chat")
    st.markdown(f"<br>{t('line_settings')}", unsafe_allow_html=True)
    ln_token   = st.text_input(t("line_token"),   value=settings.get("line_token",""), type="password", key="ln_tok")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("save_notify"), use_container_width=True):
            save_notification_settings(tg_token, tg_chat_id, ln_token)
            st.success(t("notify_saved"))
    with c2:
        if st.button(t("test_notify"), use_container_width=True):
            save_notification_settings(tg_token, tg_chat_id, ln_token)
            results = test_notification()
            if results:
                for ch, ok in results.items():
                    (st.success if ok else st.error)(t("notify_ok" if ok else "notify_fail", ch=ch))
            else:
                st.warning(t("no_notify_channel"))
    st.markdown('</div>', unsafe_allow_html=True)
