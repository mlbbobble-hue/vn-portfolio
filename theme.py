import streamlit as st

def load_css():
    """
    載入全域 CSS 主題 (The Dividend Tracker 風格)
    """
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Urbanist', sans-serif !important;
}

/* 全站背景與字體顏色 (針對預設 Light Theme 但強制顯示暗色質感) */
.stApp {
    background: linear-gradient(135deg, #001F29 0%, #004B5E 50%, #002B36 100%);
    color: #F7F9FC;
}

/* 針對 Streamlit 內建的深色模式優化 */
@media (prefers-color-scheme: dark) {
    .stApp {
        background: linear-gradient(180deg, #021c23 0%, #063442 100%);
        color: #F7F9FC;
    }
}

/* 側邊欄背景 */
[data-testid="stSidebar"] {
    background: rgba(0, 31, 41, 0.8) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

/* 卡片與 Metric 玻璃擬態風格 (Glassmorphism) */
.card, [data-testid="metric-container"], div.css-1r6slb0 {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    padding: 20px 24px;
    margin: 8px 0;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    transition: transform 0.2s ease-in-out;
}

.card:hover, [data-testid="metric-container"]:hover {
    transform: translateY(-3px);
}

/* 標題與重點文字的漸層高亮 */
.highlight-text {
    background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}

/* 按鈕風格 */
.stButton>button {
    background: linear-gradient(135deg, #068BAA, #007E9C) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background 0.3s ease;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #007E9C, #005A70) !important;
    box-shadow: 0 4px 12px rgba(6, 139, 170, 0.4);
}

/* DataFrame 表格圓角 */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 特別警告或提醒區塊 (如即將除息) */
.ex-soon {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.1));
    border: 1px solid rgba(251, 191, 36, 0.3);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 4px 0;
}

/* 頁面標題容器 */
.page-header-container {
    background: linear-gradient(90deg, rgba(6, 139, 170, 0.2) 0%, transparent 100%);
    border-left: 4px solid #068BAA;
    padding: 12px 20px;
    border-radius: 0 12px 12px 0;
    margin-bottom: 24px;
}

h1, h2, h3 {
    color: #FFFFFF !important;
}

p, span, label {
    color: #E2E8F0;
}

</style>""", unsafe_allow_html=True)
