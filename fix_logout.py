import re

with open("auth_page.py", "r", encoding="utf-8") as f:
    content = f.read()

target_logout = """    if st.button(f"🚪 {t('logout')}", use_container_width=True, type="secondary"):
        from supabase_db import sign_out
        sign_out()
        for key in ["authenticated", "user_id", "user_email", "user_name", "access_token"]:
            st.session_state.pop(key, None)
        st.rerun()"""

new_logout = """    if st.button(f"🚪 {t('logout')}", use_container_width=True, type="secondary"):
        from supabase_db import sign_out
        sign_out()
        for key in ["authenticated", "user_id", "user_email", "user_name", "access_token"]:
            st.session_state.pop(key, None)
        
        import streamlit.components.v1 as components
        components.html("<script>document.cookie = 'sb_refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'; setTimeout(function(){ window.parent.location.reload(); }, 500);</script>")"""

if target_logout in content:
    content = content.replace(target_logout, new_logout)
    with open("auth_page.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Logout cookie clearing added.")
else:
    print("Logout block not found.")
