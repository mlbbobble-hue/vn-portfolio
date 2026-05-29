"""頁面6：管理員後台（開通帳號）"""
import streamlit as st
import pandas as pd
from auth_page import check_auth, render_user_info_sidebar
from supabase_db import sb_get_all_users_approval, sb_update_user_approval, is_supabase_available

st.set_page_config(page_title="VN Portfolio | 管理員後台", page_icon="⚙️", layout="wide")
from theme import load_css
load_css()


# 檢查是否登入與審核
if not check_auth():
    st.stop()

# 檢查管理員權限
if not st.session_state.get("is_admin", False):
    st.error("🚫 您沒有權限訪問此頁面。")
    st.stop()

st.markdown("""
<div class="page-header">
    <h2>⚙️ 系統管理員後台</h2>
    <p>審核並開通新用戶的登入權限。</p>
</div>""", unsafe_allow_html=True)

if not is_supabase_available():
    st.info("本機開發模式下，沒有真實的審核名單。")
    st.stop()

admin_id = st.session_state["user_id"]
df = sb_get_all_users_approval(admin_id)

if df.empty:
    st.info("目前沒有任何用戶註冊紀錄。")
    st.stop()

# 狀態統計
total_users = len(df)
pending_users = len(df[df["is_approved"] == False])

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div style='font-size:.82rem;color:var(--text-muted);text-transform:uppercase;'>總註冊人數</div>
        <div style='font-size:1.6rem;font-weight:700;color:var(--cathay-green);'>{total_users}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div style='font-size:.82rem;color:var(--text-muted);text-transform:uppercase;'>等待開通</div>
        <div style='font-size:1.6rem;font-weight:700;color:#f97316;'>{pending_users}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📋 用戶審核名單")

# 將 DataFrame 轉為列表渲染，以加上操作按鈕
for _, row in df.iterrows():
    u_id = row["user_id"]
    u_email = row["email"]
    is_appr = row["is_approved"]
    is_adm = row["is_admin"]
    created = pd.to_datetime(row["created_at"]).strftime("%Y-%m-%d %H:%M") if pd.notna(row["created_at"]) else ""
    
    status_icon = "✅ 已開通" if is_appr else "⏳ 等待審核"
    status_color = "var(--cathay-green)" if is_appr else "#f97316"
    
    with st.container():
        st.markdown(f"""
        <div class="card" style='display:flex; justify-content:space-between; align-items:center; padding: 16px 20px; margin-bottom: 10px;'>
            <div>
                <div style='font-size:1.1rem; font-weight:600; color:var(--text-primary);'>{u_email} {"👑 (管理員)" if is_adm else ""}</div>
                <div style='font-size:0.85rem; color:var(--text-muted); margin-top:4px;'>註冊時間: {created} | ID: {u_id[:8]}...</div>
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
                if st.button("✅ 允許登入", key=f"appr_{u_id}", use_container_width=True):
                    sb_update_user_approval(admin_id, u_id, True)
                    st.success(f"已開通 {u_email} 的權限！")
                    st.rerun()
        else:
            with col1:
                if not is_adm: # 避免管理員把自己的權限關掉
                    if st.button("❌ 撤銷權限", key=f"revoke_{u_id}", use_container_width=True):
                        sb_update_user_approval(admin_id, u_id, False)
                        st.warning(f"已撤銷 {u_email} 的權限！")
                        st.rerun()
