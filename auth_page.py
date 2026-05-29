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
.auth-logo .icon { font-size: 3.5rem; }
.auth-logo .title {
    font-size: 1.5rem; font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 8px 0 4px;
}
.auth-logo .sub { font-size: 0.85rem; color: #64748b; }
.auth-card {
    background: var(--cathay-white); box-shadow: var(--shadow-soft);
    border: 1px solid rgba(0,163,82,0.3);
    border-radius: 20px;
    padding: 32px 36px;
    backdrop-filter: blur(20px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.auth-title {
    font-size: 1.3rem; font-weight: 600; color: var(--text-primary);
    margin-bottom: 24px; text-align: center;
}
.stTextInput > div > div > input {
    background: rgba(15,15,35,0.8) !important;
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
    color: #a78bfa !important;
    box-shadow: none !important;
}
.divider {
    text-align: center; color: #475569; font-size: 0.85rem;
    margin: 16px 0; position: relative;
}
.divider::before, .divider::after {
    content: ''; position: absolute; top: 50%; width: 42%; height: 1px;
    background: rgba(0,163,82,0.2);
}
.divider::before { left: 0; }
.divider::after { right: 0; }
.footer-note {
    text-align: center; color: #475569; font-size: 0.75rem; margin-top: 20px;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1e3a 0%, #16213e 100%);
    border-right: 1px solid rgba(0,163,82,0.2);
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
        <div class="icon">📈</div>
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
    檢查當前 session 是否已驗證。
    若未驗證，渲染登入頁並回傳 False。
    若已驗證，回傳 True（App 繼續渲染）。
    """
    from supabase_db import is_supabase_available

    # 本機開發模式（無 Supabase 設定）：自動以訪客身份登入
    if not is_supabase_available():
        if not st.session_state.get("authenticated"):
            st.session_state["authenticated"] = True
            st.session_state["user_id"]    = "local_dev_user"
            st.session_state["user_email"] = "dev@localhost"
            st.session_state["user_name"]  = "本機開發者"
        return True

    # 已登入
    if st.session_state.get("authenticated") and st.session_state.get("user_id"):
        return True

    # 未登入 → 顯示登入頁
    render_auth_page()
    return False


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
