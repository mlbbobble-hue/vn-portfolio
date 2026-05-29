"""
auth_page.py — 登入/註冊頁面（Supabase Auth）
"""
import streamlit as st
from i18n import t, render_lang_switcher, get_lang


# ── 全域樣式（登入頁專用）─────────────────────────────────────
AUTH_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background: var(--background-main);
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
    width: 64px; height: 64px; fill: var(--cathay-green);
}
.auth-logo .title {
    font-size: 1.5rem; font-weight: 700;
    color: var(--cathay-green);
    margin: 8px 0 4px;
}
.auth-logo .sub { font-size: 0.85rem; color: var(--text-muted); }
.auth-card {
    background: var(--card-bg); 
    border: 1px solid rgba(0,163,82,0.2);
    border-radius: 20px;
    padding: 32px 36px;
    backdrop-filter: blur(20px);
    box-shadow: var(--shadow-soft);
}
.auth-title {
    font-size: 1.3rem; font-weight: 600; color: var(--text-primary);
    margin-bottom: 24px; text-align: center;
}
.stTextInput > div > div > input {
    background: var(--background-main) !important;
    border: 1px solid rgba(0,163,82,0.3) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--cathay-green) !important;
    box-shadow: 0 0 0 2px rgba(0,163,82,0.25) !important;
}
.stButton > button {
    background: var(--cathay-green) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 1rem !important; padding: 12px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(0,163,82,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0,163,82,0.5) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(0,163,82,0.4) !important;
    color: var(--cathay-green) !important;
    box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(0,163,82,0.05) !important;
}
.divider {
    text-align: center; color: var(--text-muted); font-size: 0.85rem;
    margin: 16px 0; position: relative;
}
.divider::before, .divider::after {
    content: ''; position: absolute; top: 50%; width: 42%; height: 1px;
    background: rgba(0,163,82,0.2);
}
.divider::before { left: 0; }
.divider::after { right: 0; }
.footer-note {
    text-align: center; color: var(--text-muted); font-size: 0.75rem; margin-top: 20px;
}
</style>
"""


def render_auth_page():
    """
    渲染完整登入/註冊頁面。
    若登入成功，將 session_state 設定好後 rerun。
    回傳 False 表示用戶未登入（App 應停止渲染後續頁面）。
    """
    st.markdown(AUTH_STYLE, unsafe_allow_html=True)

    # 側邊欄：語言切換
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:12px 0;'>
            <div style='font-size:2rem;'>📈</div>
            <div style='font-size:.9rem;color:#64748b;'>VN Portfolio</div>
        </div>
        """, unsafe_allow_html=True)
        render_lang_switcher()

    # Logo 區
    st.markdown(f"""
    <div class="auth-container">
    <div class="auth-logo">
        <div class="icon"><svg width="64" height="64" viewBox="0 0 24 24" fill="var(--cathay-green)" xmlns="http://www.w3.org/2000/svg"><path d="M17 12C18.6569 12 20 10.6569 20 9C20 7.34315 18.6569 6 17 6C16.8202 6 16.6441 6.01579 16.4727 6.04618C15.8291 3.75549 13.6895 2 11.1111 2C8.53272 2 6.39308 3.75549 5.74945 6.04618C5.57811 6.01579 5.40194 6 5.22222 6C3.44263 6 2 7.34315 2 9C2 10.6569 3.44263 12 5.22222 12C5.35209 12 5.47955 11.9922 5.60421 11.977C6.07921 13.7277 7.72895 15 9.66667 15H10.5556V20C10.5556 21.1046 11.451 22 12.5556 22H13.4444C13.9967 22 14.4444 21.5523 14.4444 21V15H15.3333C17.2711 15 18.9208 13.7277 19.3958 11.977C19.5205 11.9922 19.6479 12 19.7778 12H17Z"/></svg></div>
        <div class="title">{t('app_name')}</div>
        <div class="sub">{t('app_tagline')}</div>
    </div>
    """, unsafe_allow_html=True)

    # Tab：登入 / 註冊
    tab_login, tab_register = st.tabs([f"🔐 {t('login')}", f"✨ {t('register')}"])

    # ── 登入 Tab ──────────────────────────────────────────────
    with tab_login:
        st.markdown(f'<div class="auth-card"><div class="auth-title">{t("login_title")}</div>', unsafe_allow_html=True)

        login_email = st.text_input(t("email"), placeholder="you@example.com", key="login_email")
        login_pw    = st.text_input(t("password"), type="password", key="login_pw")

        col1, col2 = st.columns([3, 2])
        with col1:
            login_btn = st.button(t("login_btn"), use_container_width=True, key="do_login")
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
                    st.success(t("login_success", name=full_name))
                    st.rerun()
                elif result["error"] == "EMAIL_NOT_CONFIRMED":
                    st.warning(t("check_email_confirm"))
                else:
                    st.error(t("login_fail"))

        if forgot_btn and login_email:
            from supabase_db import reset_password
            if reset_password(login_email.strip()):
                st.info("📧 重設密碼連結已發送至您的 Email" if get_lang()=="zh" else "📧 Đã gửi link đặt lại mật khẩu đến email của bạn")

        
        st.markdown('<div class="divider">OR</div>', unsafe_allow_html=True)
        if st.button("🚀 使用 Google 帳號一鍵登入", use_container_width=True):
            from supabase_db import sign_in_with_google
            res = sign_in_with_google()
            if res.get("success"):
                st.markdown(f'<meta http-equiv="refresh" content="0;url={res["url"]}">', unsafe_allow_html=True)
            else:
                st.error(t("login_fail"))

        st.markdown("</div>", unsafe_allow_html=True)

    # ── 註冊 Tab ──────────────────────────────────────────────
    with tab_register:
        st.markdown(f'<div class="auth-card"><div class="auth-title">{t("register_title")}</div>', unsafe_allow_html=True)

        reg_name  = st.text_input(t("full_name"), placeholder="Nguyễn Văn A / 王小明", key="reg_name")
        reg_email = st.text_input(t("email"), placeholder="you@example.com", key="reg_email")
        reg_pw    = st.text_input(t("password"), type="password",
                                   placeholder="至少 6 個字元" if get_lang()=="zh" else "Tối thiểu 6 ký tự",
                                   key="reg_pw")
        reg_pw2   = st.text_input(t("confirm_password"), type="password", key="reg_pw2")

        reg_btn = st.button(t("register_btn"), use_container_width=True, key="do_register")

        if reg_btn:
            if not all([reg_name, reg_email, reg_pw, reg_pw2]):
                st.error(t("fill_all_fields"))
            elif reg_pw != reg_pw2:
                st.error(t("password_mismatch"))
            elif len(reg_pw) < 6:
                st.error("密碼至少需要 6 個字元" if get_lang()=="zh" else "Mật khẩu tối thiểu 6 ký tự")
            else:
                with st.spinner(t("loading")):
                    from supabase_db import sign_up
                    result = sign_up(reg_email.strip(), reg_pw, reg_name.strip())

                if result["success"]:
                    st.success(t("register_success"))
                    st.balloons()
                else:
                    st.error(t("register_fail", msg=result["error"]))

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # auth-container
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

    # 攔截 Google OAuth 回傳的 code
    if "code" in st.query_params:
        code = st.query_params.get("code")
        st.query_params.clear()
        with st.spinner("驗證 Google 登入中..."):
            res = exchange_code(code)
            if res.get("success"):
                user = res["user"]
                st.session_state["authenticated"] = True
                st.session_state["user_id"]       = user.id
                st.session_state["user_email"]    = user.email
                st.session_state["user_name"]     = (user.user_metadata or {}).get("full_name", user.email)
                st.session_state["access_token"]  = res["session"].access_token

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
        st.markdown("""
        <div style='max-width: 500px; margin: 100px auto; text-align: center; background: var(--cathay-white); padding: 40px; border-radius: 20px; box-shadow: var(--shadow-soft); border: 1px solid rgba(0,163,82,0.3);'>
            <div style='font-size: 4rem; margin-bottom: 20px;'>⏳</div>
            <h2 style='color: var(--text-primary); margin-bottom: 10px;'>等待管理員開通</h2>
            <p style='color: var(--text-secondary); line-height: 1.6;'>
                您的帳號已經成功登入，但由於系統採用白名單制，<br>
                目前需要等待管理員審核並開通權限。<br><br>
                系統已經發送通知信給管理員，開通後請重新整理網頁。
            </p>
            <br>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 登出", type="secondary"):
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
        st.rerun()
