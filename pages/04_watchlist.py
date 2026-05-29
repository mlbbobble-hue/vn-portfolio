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
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);color:#e2e8f0;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1e1e3a 0%,#16213e 100%);border-right:1px solid rgba(99,102,241,0.2);}
.card{background:linear-gradient(135deg,rgba(30,30,60,0.8),rgba(20,20,45,0.9));border:1px solid rgba(99,102,241,0.3);border-radius:16px;padding:20px 24px;margin:8px 0;}
.stButton>button{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border:none;border-radius:8px;font-weight:500;}
.stButton>button[kind="secondary"]{background:transparent!important;border:1px solid rgba(99,102,241,0.4)!important;color:#a78bfa!important;}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    render_lang_switcher()
    st.divider()
    render_user_info_sidebar()

if not check_auth():
    st.stop()

st.markdown(f"""
<div style='background:linear-gradient(90deg,rgba(99,102,241,0.15) 0%,transparent 100%);
            border-left:4px solid #6366f1;padding:12px 20px;border-radius:0 12px 12px 0;margin-bottom:24px;'>
    <h2 style='margin:0;color:#e2e8f0;'>{t('watchlist_title')}</h2>
    <p style='margin:4px 0 0;color:#94a3b8;font-size:0.9rem;'>{t('watchlist_desc')}</p>
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
        for _, item in wl.iterrows():
            sym = item["symbol"]
            cur_price = price_map.get(sym,{}).get("price",0)
            change    = price_map.get(sym,{}).get("change_pct",0)
            target    = item.get("target_price") or 0
            enabled   = bool(item.get("alert_enabled",1))
            dist_str  = ""; dist_color = "#94a3b8"
            if target > 0 and cur_price > 0:
                dp = (cur_price-target)/target*100
                dist_str = t("dist_to_target", pct=dp)
                dist_color = "#34d399" if dp<=2 else "#fbbf24" if dp<=10 else "#94a3b8"
            annual_dps = dps_map.get(sym, 0)
            ey_str = ""
            if annual_dps > 0 and cur_price > 0:
                ey_str = f"　{t('est_yield_label', y=get_estimated_yield(sym, cur_price, annual_dps))}"
            price_str = f"{cur_price:,.0f} {t('vnd')}" if cur_price > 0 else "─"
            cc = "#34d399" if change>0 else "#f87171" if change<0 else "#94a3b8"
            cs = "▲" if change>0 else "▼" if change<0 else "─"
            badges = []
            if target > 0: badges.append(t("target_price_label", p=target))
            if item.get("ma60_alert"): badges.append(t("ma60_alert"))
            thresh = item.get("yield_threshold")
            if thresh: badges.append(t("yield_threshold", pct=thresh*100))
            badge_str = "　".join(badges) if badges else t("no_alert")
            st.markdown(f"""
            <div style='background:rgba(30,30,60,0.7);border:1px solid rgba(99,102,241,0.25);
                        border-radius:12px;padding:14px 18px;margin:6px 0;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        {"🟢" if enabled else "⚫"} <b style='color:#a78bfa;font-size:1.05rem;'>{sym}</b>
                        <span style='color:#e2e8f0;margin-left:12px;'>{price_str}</span>
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
