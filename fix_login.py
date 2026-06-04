import re

with open("auth_page.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    # 初始化 CookieController
    try:
        from streamlit_cookies_controller import CookieController
        cookie_ctrl = CookieController()
    except Exception:
        cookie_ctrl = None

    # 自動登入邏輯
    if not st.session_state.get("authenticated") and cookie_ctrl is not None:
        saved_token = cookie_ctrl.get("sb_refresh_token")"""

new_code = """    # 初始化 CookieController
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
        saved_token = cookie_ctrl.get("sb_refresh_token")"""

if target in content:
    content = content.replace(target, new_code)
    with open("auth_page.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("auth_page.py updated for auto-login")
else:
    print("Target not found in auth_page.py")
