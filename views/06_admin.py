"""頁面6：管理員後台（開通帳號）"""
import streamlit as st
import pandas as pd
from auth_page import check_auth, render_user_info_sidebar
from supabase_db import sb_get_all_users_approval, sb_update_user_approval, is_supabase_available

from i18n import t

st.set_page_config(page_title="VN Portfolio | Admin", page_icon="⚙️", layout="wide")
from theme import load_css
load_css()


# 檢查是否登入與審核
if not check_auth():
    st.stop()

# 檢查管理員權限
if not st.session_state.get("is_admin", False):
    st.error(t("no_admin_perm"))
    st.stop()

st.markdown(f"""
<div class="page-header">
    <h2>⚙️ {t("admin_page_title")}</h2>
    <p>{t("admin_page_desc")}</p>
</div>""", unsafe_allow_html=True)

if not is_supabase_available():
    st.info(t("no_real_users"))
    st.stop()

admin_id = st.session_state["user_id"]
df = sb_get_all_users_approval(admin_id)

if df.empty:
    st.info(t("no_users_reg"))
    st.stop()

# 狀態統計
total_users = len(df)
pending_users = len(df[df["is_approved"] == False])

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div style='font-size:.82rem;color:var(--text-muted);text-transform:uppercase;'>{t("total_reg_users")}</div>
        <div style='font-size:1.6rem;font-weight:700;color:var(--cathay-green);'>{total_users}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div style='font-size:.82rem;color:var(--text-muted);text-transform:uppercase;'>{t("wait_approval")}</div>
        <div style='font-size:1.6rem;font-weight:700;color:#f97316;'>{pending_users}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.subheader(t("user_approval_list"))

# 將 DataFrame 轉為列表渲染，以加上操作按鈕
for _, row in df.iterrows():
    u_id = row["user_id"]
    u_email = row["email"]
    is_appr = row["is_approved"]
    is_adm = row["is_admin"]
    created = pd.to_datetime(row["created_at"]).strftime("%Y-%m-%d %H:%M") if pd.notna(row["created_at"]) else ""
    
    status_icon = t("is_approved") if is_appr else t("wait_review")
    status_color = "var(--cathay-green)" if is_appr else "#f97316"
    
    with st.container():
        st.markdown(f"""
        <div class="card" style='display:flex; justify-content:space-between; align-items:center; padding: 16px 20px; margin-bottom: 10px;'>
            <div>
                <div style='font-size:1.1rem; font-weight:600; color:var(--text-primary);'>{u_email} {t("admin_role") if is_adm else ""}</div>
                <div style='font-size:0.85rem; color:var(--text-muted); margin-top:4px;'>{t("reg_time")} {created} | ID: {u_id[:8]}...</div>
            </div>
            <div style='display:flex; align-items:center; gap: 16px;'>
                <div style='color:{status_color}; font-weight:600;'>{status_icon}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 加上切換按鈕
        col1, col2, _ = st.columns([1, 1, 8])
        if not is_appr:
            with col1:
                if st.button(t("allow_login"), key=f"appr_{u_id}", use_container_width=True):
                    sb_update_user_approval(admin_id, u_id, True)
                    st.success(t("granted_perm", email=u_email))
                    st.rerun()
        else:
            with col1:
                if not is_adm: # 避免管理員把自己的權限關掉
                    if st.button(t("revoke_perm"), key=f"revoke_{u_id}", use_container_width=True):
                        sb_update_user_approval(admin_id, u_id, False)
                        st.warning(t("revoked_perm", email=u_email))
                        st.rerun()
