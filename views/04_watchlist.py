"""頁面4：觀察清單（雙語 + db_router）"""
import streamlit as st
import pandas as pd
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (get_watchlist, upsert_watchlist, delete_watchlist,
                        save_notification_settings, load_notification_settings,
                        get_price_cache, upsert_price_cache)
from market_data import get_stock_price, get_moving_average
from alerts import test_notification, check_and_fire_alerts
from portfolio import get_estimated_yield, get_dividend_income_summary

st.set_page_config(page_title=f"VN Portfolio | {t('watchlist_title')}", page_icon="🔔", layout="wide")
from theme import load_css
load_css()

if not check_auth():
    st.stop()

st.markdown(f"""
<div class="page-header">
    <h2>{t('watchlist_title')}</h2>
    <p>{t('watchlist_desc')}</p>
</div>""", unsafe_allow_html=True)

tab_wl, tab_add, tab_notify = st.tabs([t("tab_watchlist"), t("tab_add_watch"), t("tab_notify")])

# ── Tab 1: 觀察清單 ─────────────────────────────────────────
with tab_wl:
    wl = get_watchlist()
    price_cache = get_price_cache()
    price_map = {}
    if not price_cache.empty:
        price_map = price_cache.set_index("symbol")[["price","change_pct"]].to_dict("index")
    try:
        div_summary = get_dividend_income_summary(wl["symbol"].tolist() if not wl.empty else [])
        dps_map = {} if div_summary.empty else div_summary.set_index("symbol")["annual_dps"].to_dict()
    except Exception:
        dps_map = {}

    if wl.empty:
        st.info(t("no_watchlist"))
    else:
        st.subheader(t("watching_count", n=len(wl)))
        
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
                    
        st.markdown("<br>", unsafe_allow_html=True)
        for _, item in wl.iterrows():
            sym = item["symbol"]
            cur_price = price_map.get(sym,{}).get("price",0)
            change    = price_map.get(sym,{}).get("change_pct",0)
            target    = item.get("target_price") or 0
            enabled   = bool(item.get("alert_enabled",1))
            dist_str  = ""; dist_color = "#D8B4E2"
            if target > 0 and cur_price > 0:
                dp = (cur_price-target)/target*100
                dist_str = t("dist_to_target", pct=dp)
                dist_color = "#FF2A85" if dp<=2 else "#9D4EDD" if dp<=10 else "#D8B4E2"
            annual_dps = dps_map.get(sym, 0)
            ey_str = ""
            if annual_dps > 0 and cur_price > 0:
                ey_str = f"　{t('est_yield_label', y=get_estimated_yield(sym, cur_price, annual_dps))}"
            price_str = f"{cur_price:,.0f} {t('vnd')}" if cur_price > 0 else "─"
            cc = "#FF2A85" if change>0 else "#FF007F" if change<0 else "#D8B4E2"
            cs = "▲" if change>0 else "▼" if change<0 else "─"
            badges = []
            if target > 0: badges.append(t("target_price_label", p=target))
            if item.get("ma60_alert"): badges.append(t("ma60_alert"))
            thresh = item.get("yield_threshold")
            if thresh: badges.append(t("yield_threshold", pct=thresh*100))
            badge_str = "　".join(badges) if badges else t("no_alert")
            st.markdown(f"""
            <div style='class="card" style="padding:14px 18px;margin:6px 0;">
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        {"🟢" if enabled else "⚫"} <b style='color:var(--text-primary);font-size:1.05rem;'>{sym}</b>
                        <span style='color:var(--text-secondary);margin-left:12px;'>{price_str}</span>
                        <span style='color:{cc};margin-left:8px;'>{cs} {abs(change):.2f}%</span>
                    </div>
                    <div style='color:{dist_color};font-size:.9rem;'>{dist_str}</div>
                </div>
                <div style='color:#64748b;font-size:.82rem;margin-top:6px;'>{badge_str}{ey_str}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t("update_wl_price"), use_container_width=True):
                with st.spinner(t("updating")):
                    for sym in wl["symbol"].tolist():
                        p = get_stock_price(sym)
                        if p["price"] > 0:
                            upsert_price_cache(sym, p["price"], p["change_pct"], p.get("volume",0))
                st.success(t("updated_count", n=len(wl)))
                st.rerun()
        with c2:
            if st.button(t("check_alerts"), use_container_width=True):
                fired = check_and_fire_alerts()
                if fired:
                    for f in fired:
                        st.warning(t("alert_fired", sym=f["symbol"], p=f["price"]))
                else:
                    st.success(t("no_alert_fired"))

        st.markdown("---")
        del_sym = st.selectbox(t("remove_watch"), [""]+wl["symbol"].tolist())
        if del_sym and st.button(t("remove_btn", sym=del_sym), use_container_width=True):
            delete_watchlist(del_sym)
            st.rerun()

# ── Tab 2: 新增 ─────────────────────────────────────────────
with tab_add:
    st.subheader(t("add_watch_title"))
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        w_sym    = st.text_input(t("symbol"), key="w_sym").upper()
        w_target = st.number_input(t("target_price_input"), min_value=0, step=1000, value=0, key="w_target")
        w_ma60   = st.toggle(t("ma60_toggle"), key="w_ma60")
    with c2:
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

    with st.expander(t("alert_conditions")):
        st.markdown(f"""
        | {t('warning')} | Trigger | Use case |
        |---|---|---|
        | 🎯 **{t('target_price')}** | Price ≤ target | Buy on dip |
        | 📊 **MA60** | Price within ±2% of MA60 | Mean reversion |
        | 💰 **{t('yield_threshold')}** | Est. yield ≥ threshold | High yield entry |
        """)

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
