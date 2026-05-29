import streamlit as st

def load_css():
    """
    載入全域 CSS 主題 (國泰證券 Cathay Securities 風格 - 強制亮色)
    """
    st.markdown("""<style>
/* 國泰證券 (Cathay Securities) 專屬字體與色彩變數 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');

:root {
    /* 強制亮色模式 (Light Mode) 參數 - 國泰經典白底綠點綴 */
    --cathay-green: #00A850;
    --cathay-dark-green: #008f44;
    --cathay-yellow: #FFB600;
    
    --bg-main: #F3F4F6;
    --bg-sidebar: #FFFFFF;
    --bg-card: #FFFFFF;
    
    --text-primary: #333333;
    --text-secondary: #666666;
    --border-color: #E5E7EB;
    
    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

html, body, [class*="css"] {
    font-family: 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
}

.stApp {
    background: var(--bg-main) !important;
    color: var(--text-primary) !important;
}

/* 側邊欄背景 */
[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-color);
}

/* 卡片與 Metric 容器 (扁平化與極簡設計) */
.card, [data-testid="metric-container"], div.css-1r6slb0 {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 20px 24px;
    margin: 8px 0;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease-in-out;
}

.card:hover, [data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--cathay-green) !important;
}

/* 標題與重點文字高亮 */
.highlight-text {
    color: var(--cathay-green) !important;
    font-weight: 700;
}

/* 按鈕風格 (國泰企業綠) */
.stButton>button {
    background: var(--cathay-green) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: background 0.2s ease;
}

.stButton>button:hover {
    background: var(--cathay-dark-green) !important;
    box-shadow: var(--shadow-md);
}

/* DataFrame 表格圓角與框線 */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border-color);
    background: var(--bg-card);
}

/* 特別警告或提醒區塊 (如即將除息) */
.ex-soon {
    background: rgba(255, 182, 0, 0.1);
    border: 1px solid rgba(255, 182, 0, 0.5);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 0;
}

/* 頁面標題容器 (國泰左側綠色裝飾線) */
.page-header-container {
    background: var(--bg-sidebar);
    border-left: 6px solid var(--cathay-green);
    padding: 16px 24px;
    border-radius: 0 12px 12px 0;
    margin-bottom: 24px;
    box-shadow: var(--shadow-sm);
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

/* 確保特定描述文字使用次要顏色 */
p, span, label {
    color: var(--text-secondary);
}

/* Metric 內建數值強制顯示主色 */
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
}

</style>""", unsafe_allow_html=True)
