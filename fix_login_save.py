import re

with open("auth_page.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """    # 自動登入邏輯
    if not st.session_state.get("authenticated") and cookie_ctrl is not None:
        saved_token = cookie_ctrl.get("sb_refresh_token")"""

new1 = """    # 自動登入邏輯
    if not st.session_state.get("authenticated") and cookie_ctrl is not None:
        saved_token = cookies.get("sb_refresh_token") if cookies else None"""

target2 = """                    if remember_me and cookie_ctrl is not None:
                        try:
                            cookie_ctrl.set("sb_refresh_token", result["session"].refresh_token, max_age=86400*30)
                        except:
                            pass
                    st.success(t("login_success", name=full_name))
                    st.rerun()"""

new2 = """                    if remember_me and cookie_ctrl is not None:
                        try:
                            cookie_ctrl.set("sb_refresh_token", result["session"].refresh_token, max_age=86400*30)
                        except:
                            pass
                        st.success(t("login_success", name=full_name) + " (Redirecting...)")
                        import streamlit.components.v1 as components
                        components.html("<script>setTimeout(function(){ window.parent.location.reload(); }, 800);</script>")
                    else:
                        st.success(t("login_success", name=full_name))
                        st.rerun()"""

if target1 in content and target2 in content:
    content = content.replace(target1, new1)
    content = content.replace(target2, new2)
    with open("auth_page.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("auth_page.py updated for cookie saving fix")
else:
    print("Targets not found in auth_page.py")
