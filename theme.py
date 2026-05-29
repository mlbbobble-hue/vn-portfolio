import streamlit as st

def load_css():
    """
    載入全域 CSS 主題 (國泰證券 Cathay Securities 手機 App 風格)
    """
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');

:root {
    /* 國泰證券 App 配色 */
    --cathay-green: #00A352;
    --cathay-dark-green: #008241;
    --cathay-red: #E74C3C;
    --cathay-yellow: #F39C12;
    --cathay-bg-light: #F6F7F9;
    --cathay-white: #FFFFFF;
    --text-primary: #333333;
    --text-secondary: #888888;
    --border-color: #EFEFEF;
    
    --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.04);
}

html, body, [class*="css"] {
    font-family: 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
}

/* 強制隱藏 Plotly 工具列以符合手機體驗 */
.modebar {
    display: none !important;
}

.stApp {
    background-color: var(--cathay-bg-light) !important;
    color: var(--text-primary) !important;
}

/* 移除預設的頂部 padding 讓 Header 可以貼頂 */
.css-18e3th9 {
    padding-top: 0rem !important;
}

/* 頂部國泰綠 Header 樣式 */
.cathay-app-header {
    background-color: var(--cathay-green);
    color: white;
    padding: 24px 20px;
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
    margin: -1rem -1rem 20px -1rem;
    box-shadow: 0 4px 10px rgba(0, 163, 82, 0.2);
    text-align: center;
}
.cathay-app-header h1 {
    color: white !important;
    font-size: 24px;
    margin: 0;
    font-weight: 700;
}
.cathay-app-header .total-value {
    font-size: 36px;
    font-weight: 700;
    margin-top: 8px;
}

/* 白色卡片 */
.card, [data-testid="metric-container"], div.css-1r6slb0, .cathay-card {
    background-color: var(--cathay-white) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 16px !important;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-soft);
}

/* 九宮格功能區 (Quick Actions Grid) */
.quick-action-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}
.quick-action-item {
    background-color: var(--cathay-white);
    border-radius: 16px;
    padding: 16px 8px;
    text-align: center;
    box-shadow: var(--shadow-soft);
    border: 1px solid var(--border-color);
    text-decoration: none;
    color: var(--text-primary);
    transition: transform 0.1s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.quick-action-item:active {
    transform: scale(0.95);
}
.quick-action-icon {
    font-size: 32px;
    margin-bottom: 8px;
}
.quick-action-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
}

/* 膠囊按鈕 (Pill-shaped Buttons) */
.stButton>button {
    background-color: var(--cathay-green) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important; /* 膠囊形狀 */
    font-weight: 600 !important;
    padding: 8px 24px !important;
    transition: background-color 0.2s ease;
    white-space: nowrap !important;
}
.stButton>button * {
    color: white !important;
    white-space: nowrap !important;
}
.stButton>button:hover {
    background-color: var(--cathay-dark-green) !important;
}
.stButton>button:active {
    transform: scale(0.98);
}

/* 修復側邊欄與頁面連結顏色太淡的問題 */
[data-testid="stSidebarNav"] span, 
a[data-testid="stPageLink-NavLink"] p, 
a[data-testid="stPageLink-NavLink"] span {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* 將側邊欄導覽列變成 App 風格的九宮格 (大圖示) */
[data-testid="stSidebarNav"] ul {
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 12px !important;
    padding: 16px !important;
}
[data-testid="stSidebarNav"] li {
    background-color: var(--cathay-white) !important;
    border-radius: 16px !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: var(--shadow-soft) !important;
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stSidebarNav"] a {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 16px 8px !important;
    background-color: transparent !important;
    gap: 8px !important;
}
/* 強制覆蓋被選中的背景色 */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(0, 163, 82, 0.05) !important;
    border-radius: 16px !important;
    border: 1px solid var(--cathay-green) !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] span {
    color: var(--cathay-green) !important;
    font-weight: 700 !important;
}
[data-testid="stSidebarNav"] a > span:first-child { /* icon span */
    font-size: 32px !important;
    margin: 0 !important;
    line-height: 1 !important;
}
[data-testid="stSidebarNav"] a > span:last-child { /* text span */
    font-size: 13px !important;
    margin-top: 4px !important;
    text-align: center !important;
    white-space: normal !important;
    line-height: 1.2 !important;
}

/* 報酬率徽章 (Badges) */
.badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 14px;
}
.badge-up {
    background-color: rgba(0, 163, 82, 0.1);
    color: var(--cathay-green);
}
.badge-down {
    background-color: rgba(231, 76, 60, 0.1);
    color: var(--cathay-red);
}
.badge-neutral {
    background-color: rgba(136, 136, 136, 0.1);
    color: var(--text-secondary);
}

/* DataFrame 表格優化 */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border-color);
    background-color: var(--cathay-white);
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

p, span, label {
    color: var(--text-secondary);
}

/* Metric 標籤與數值 */
[data-testid="stMetricLabel"] {
    font-size: 14px !important;
    color: var(--text-secondary) !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 24px !important;
}

/* 新增HOT標籤 */
.badge-hot {
    background-color: var(--cathay-red);
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    position: absolute;
    top: -10px;
    right: -10px;
    font-weight: 700;
}

</style>""", unsafe_allow_html=True)
