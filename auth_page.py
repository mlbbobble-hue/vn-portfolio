"""
auth_page.py — 登入/註冊頁面（Supabase Auth）
"""
import streamlit as st

import base64
try:
    with open("assets/logo.png", "rb") as _f:
        logo_base64 = base64.b64encode(_f.read()).decode()
except:
    logo_base64 = ""


import base64
try:
    with open("assets/logo.png", "rb") as _f:
        logo_base64 = base64.b64encode(_f.read()).decode()
except:
    logo_base64 = ""

from i18n import t, render_lang_switcher, get_lang


# ── 全域樣式（登入頁專用）─────────────────────────────────────
AUTH_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background: var(--bg-main, #0f172a);
    min-height: 100vh;
}
.auth-container {
    max-width: 460px;
    margin: 0 auto;
    padding: 40px 20px;
}
.auth-logo {
    text-align: center;
    margin-bottom: 32px;
}
.auth-logo .icon { 
    display: flex; justify-content: center; margin-bottom: 12px;
}
.auth-logo .icon svg {
    width: 64px; height: 64px; fill: var(--financial-up, #10b981);
}
.auth-logo .title {
    font-size: 1.5rem; font-weight: 700;
    color: var(--financial-up, #10b981);
    margin: 8px 0 4px;
}
.auth-logo .sub { font-size: 0.85rem; color: var(--text-secondary, #94a3b8); }
.auth-card {
    background: var(--bg-card, #1e293b); 
    border: 1px solid var(--border-color, #334155);
    border-radius: 12px;
    padding: 32px 36px;
    backdrop-filter: blur(20px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
.auth-title {
    font-size: 1.3rem; font-weight: 600; color: var(--text-primary, #f8fafc);
    margin-bottom: 24px; text-align: center;
}
.stTextInput > div > div > input {
    background: var(--bg-main, #0f172a) !important;
    border: 1px solid var(--border-color, #334155) !important;
    border-radius: 10px !important;
    color: var(--text-primary, #f8fafc) !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--financial-up, #10b981) !important;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25) !important;
}
.stButton > button {
    background: var(--financial-up, #10b981) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 1rem !important; padding: 12px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(16, 185, 129, 0.4) !important;
    color: var(--financial-up, #10b981) !important;
    box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(16, 185, 129, 0.1) !important;
}
.stCheckbox > label {
    color: var(--text-secondary, #94a3b8) !important;
}
.divider {
    text-align: center; color: var(--text-secondary, #94a3b8); font-size: 0.85rem;
    position: relative; margin: 24px 0;
}
.divider::before, .divider::after {
    content: ""; position: absolute; top: 50%; width: 42%;
    border-top: 1px solid var(--border-color, #334155);
}
.divider::before { left: 0; }
.divider::after { right: 0; }
.auth-switch {
    text-align: center; margin-top: 16px; font-size: 0.9rem;
    color: var(--text-secondary, #94a3b8);
}
.auth-switch a {
    color: var(--financial-up, #10b981); font-weight: 600; text-decoration: none; cursor: pointer;
}
.footer-note {
    text-align: center; color: var(--text-secondary, #94a3b8); font-size: 0.75rem; margin-top: 20px;
}

[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }

/* 將 Tabs 容器變成卡片風格 */
[data-testid="stTabs"] {
    background: var(--bg-card, #1e293b);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    border: 1px solid var(--border-color, #334155);
}
[data-testid="stTabs"] button {
    color: var(--text-secondary, #94a3b8) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--financial-up, #10b981) !important;
}

</style>

"""



def render_auth_page():
    # 初始化 CookieController
    try:
        from streamlit_cookies_controller import CookieController
        cookie_ctrl = CookieController()
    except Exception:
        cookie_ctrl = None

    # 等待前端傳回 Cookie，避免第一次加載時瞬間顯示登入畫面
    if cookie_ctrl is not None and not st.session_state.get("authenticated"):
        cookies = cookie_ctrl.getAll()
        if cookies is None:
            st.spinner(t("loading"))
            st.stop() # 停止渲染，等待組件觸發 re-run

    # 自動登入邏輯
    if not st.session_state.get("authenticated") and cookie_ctrl is not None:
        saved_token = cookies.get("sb_refresh_token") if cookies else None
        if saved_token and "auto_login_attempted" not in st.session_state:
            st.session_state["auto_login_attempted"] = True
            from supabase_db import refresh_login
            res = refresh_login(saved_token)
            if res["success"]:
                user = res["user"]
                full_name = (user.user_metadata or {}).get("full_name", user.email)
                st.session_state["authenticated"] = True
                st.session_state["user_id"]       = user.id
                st.session_state["user_email"]    = user.email
                st.session_state["user_name"]     = full_name
                st.session_state["access_token"]  = res["session"].access_token
                # 更新 token
                cookie_ctrl.set("sb_refresh_token", res["session"].refresh_token, max_age=86400*30)
                st.rerun()


    """
    渲染完整登入/註冊頁面。
    若登入成功，將 session_state 設定好後 rerun。
    回傳 False 表示用戶未登入（App 應停止渲染後續頁面）。
    """
    st.markdown(AUTH_STYLE, unsafe_allow_html=True)



    # 頂部語言切換
    current = get_lang()
    options = ["🇹🇼 繁體中文", "🇻🇳 Tiếng Việt"]
    current_index = 0 if current == "zh" else 1
    
    col1, col2 = st.columns([7, 3])
    with col2:
        selected = st.selectbox("Language", options, index=current_index, label_visibility="collapsed")
        new_lang = "zh" if "繁體中文" in selected else "vi"
        if new_lang != current:
            from i18n import set_lang
            set_lang(new_lang)
            st.rerun()

    # Logo 區
    st.markdown(f"""
    <div class="auth-container">
    <div class="auth-logo">
        <div class="icon"><img src="data:image/png;base64,{logo_base64}"   style="width: 250px; height: 250px; border-radius: 12px;"></div>
        
        
    </div>
    """, unsafe_allow_html=True)

    # Tab：登入 / 註冊
    tab_login, tab_register = st.tabs([f"🔐 {t('login')}", f"✨ {t('register')}"])

    # ── 登入 Tab ──────────────────────────────────────────────
    with tab_login:
        st.subheader(t("login_title"))
        

        login_email = st.text_input(t("email"), placeholder="you@example.com", key="login_email")
        login_pw    = st.text_input(t("password"), type="password", key="login_pw")

        remember_me = st.checkbox("保持登入狀態 (Keep me logged in)", value=True)
        col1, col2 = st.columns([3, 2])
        with col1:
            login_btn = st.button(t("login_btn"), use_container_width=True, key="do_login", type="primary")
        with col2:
            forgot_btn = st.button("🔑 Forgot?" if get_lang()=="vi" else "🔑 忘記密碼?",
                                    use_container_width=True, key="forgot_btn",
                                    type="secondary")

        if login_btn:
            if not login_email or not login_pw:
                st.error(t("fill_all_fields"))
            else:
                with st.spinner(t("loading")):
                    from supabase_db import sign_in
                    result = sign_in(login_email.strip(), login_pw)

                if result["success"]:
                    user = result["user"]
                    full_name = (user.user_metadata or {}).get("full_name", user.email)
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"]       = user.id
                    st.session_state["user_email"]    = user.email
                    st.session_state["user_name"]     = full_name
                    st.session_state["access_token"]  = result["session"].access_token
                    if remember_me and cookie_ctrl is not None:
                        try:
                            cookie_ctrl.set("sb_refresh_token", result["session"].refresh_token, max_age=86400*30)
                        except:
                            pass
                        st.success(t("login_success", name=full_name) + " (Redirecting...)")
                        import streamlit.components.v1 as components
                        components.html("<script>setTimeout(function(){ window.parent.location.reload(); }, 800);</script>")
                    else:
                        st.success(t("login_success", name=full_name))
                        st.rerun()
                elif result["error"] == "EMAIL_NOT_CONFIRMED":
                    st.warning(t("check_email_confirm"))
                else:
                    st.error(t("login_fail"))

                       if forgot_btn:
            if not login_email:
                st.error(t("enter_email_first"))
            else:
                from supabase_db import reset_password
                if reset_password(login_email.strip()):
                                        st.info(t("reset_pwd_sent"))
                else:
                                        st.error(t("reset_pwd_fail"))
                    # ── 註冊 Tab ──────────────────────────────────────────────
    with tab_register:
        st.subheader(t("register_title"))
        

        reg_name  = st.text_input(t("full_name"), placeholder="Nguyễn Văn A / 王小明", key="reg_name")
        reg_email = st.text_input(t("email"), placeholder="you@example.com", key="reg_email")
        reg_pw    = st.text_input(t("password"), type="password",
                                   placeholder="至少 6 個字元" if get_lang()=="zh" else "Tối thiểu 6 ký tự",
                                   key="reg_pw")
        reg_pw2   = st.text_input(t("confirm_password"), type="password", key="reg_pw2")

        reg_btn = st.button(t("register_btn"), use_container_width=True, key="do_register", type="primary")

        if reg_btn:
            if not all([reg_name, reg_email, reg_pw, reg_pw2]):
                st.error(t("fill_all_fields"))
            elif reg_pw != reg_pw2:
                st.error(t("password_mismatch"))
            elif len(reg_pw) < 6:
                st.error(t("pwd_min_len"))
            else:
                with st.spinner(t("loading")):
                    from supabase_db import sign_up
                    result = sign_up(reg_email.strip(), reg_pw, reg_name.strip())

                if result["success"]:
                    st.success(t("register_success"))
                    st.balloons()
                else:
                    st.error(t("register_fail", msg=result["error"]))

        

      # auth-container
    st.markdown(f'<div class="footer-note">{t("disclaimer")}</div>', unsafe_allow_html=True)

    return False  # 未登入


def check_auth() -> bool:
    """
    檢查當前 session 是否已驗證與審核。
    若未驗證，渲染登入頁並回傳 False。
    若已驗證但未審核，顯示等待開通頁面並回傳 False。
    若已驗證且已審核，回傳 True（App 繼續渲染）。
    """
    from supabase_db import is_supabase_available, exchange_code, sb_check_approval



    # 本機開發模式（無 Supabase 設定）：自動以訪客身份登入
    if not is_supabase_available():
        if not st.session_state.get("authenticated"):
            st.session_state["authenticated"] = True
            st.session_state["user_id"]    = "local_dev_user"
            st.session_state["user_email"] = "dev@localhost"
            st.session_state["user_name"]  = "本機開發者"
            st.session_state["is_admin"]   = True
        return True

    # 尚未登入
    if not st.session_state.get("authenticated") or not st.session_state.get("user_id"):
        render_auth_page()
        return False

    # 已經登入，檢查審核狀態
    user_id = st.session_state["user_id"]
    email = st.session_state["user_email"]
    
    # 避免每次重新整理都去資料庫查，使用 session 暫存
    # 👑 硬編碼最高管理員免審核通道
    if email == "mlbbobble@gmail.com":
        st.session_state["is_approved"] = True
        st.session_state["is_admin"] = True
        return True

    if "is_approved" not in st.session_state:
        appr = sb_check_approval(user_id, email)
        if appr.get("is_new"):
            # 發送通知信
            try:
                from notifier import send_admin_notification
                send_admin_notification(email)
            except Exception:
                pass
                
        st.session_state["is_approved"] = appr.get("is_approved", False)
        st.session_state["is_admin"] = appr.get("is_admin", False)

    if not st.session_state["is_approved"]:
        st.markdown(f"""
        <div style='max-width: 500px; margin: 100px auto; text-align: center; background: var(--cathay-white); padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid rgba(0,163,82,0.3);'>
            <div style='font-size: 4rem; margin-bottom: 20px;'>⏳</div>
            <h2 style='color: #333333; margin-bottom: 10px;'>{t("wait_admin_title")}</h2>
            <p style='color: var(--text-secondary); line-height: 1.6;'>
                {t("wait_admin_desc")}
            </p>
            <br>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 " + t("logout"), type="secondary"):
            from supabase_db import sign_out
            sign_out()
            for key in ["authenticated", "user_id", "user_email", "user_name", "access_token", "is_approved", "is_admin"]:
                st.session_state.pop(key, None)
            st.rerun()
        return False

    return True


def render_user_info_sidebar():
    """在側邊欄渲染用戶資訊 + 登出按鈕"""
    from supabase_db import is_supabase_available
    if not is_supabase_available():
        return

    email = st.session_state.get("user_email", "")
    name  = st.session_state.get("user_name", email)

    st.markdown(f"""
    <div style='background:rgba(0,163,82,0.1);border:1px solid rgba(0,163,82,0.25);
                border-radius:12px;padding:10px 14px;margin:8px 0;'>
        <div style='font-size:.75rem;color:#64748b;'>{t("logged_in_as", email=email)}</div>
        <div style='font-size:.9rem;color:#a78bfa;font-weight:600;'>👤 {name}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"🚪 {t('logout')}", use_container_width=True, type="secondary"):
        from supabase_db import sign_out
        sign_out()
        for key in ["authenticated", "user_id", "user_email", "user_name", "access_token"]:
            st.session_state.pop(key, None)
        
        import streamlit.components.v1 as components
        components.html("<script>document.cookie = 'sb_refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'; setTimeout(function(){ window.parent.location.reload(); }, 500);</script>")
