import streamlit as st

def load_css():
    """
    載入全域 CSS 主題 (國泰證券 Cathay Securities 手機 App 風格)
    """
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');

:root {
    /* Synthwave 霓虹復古風與毛玻璃特效 配色 */
    --bg-main: #0B0914;       /* 星空暗紫黑大背景 */
    --bg-card: rgba(20, 18, 38, 0.6); /* 半透明深紫色 (毛玻璃) */
    --text-primary: #FFFFFF;  /* 純白主文字 */
    --text-secondary: #D8B4E2;/* 淡紫粉色次要文字 */
    
    --financial-up: #FF2A85;  /* 獲利：亮粉紅 */
    --financial-down: #9D4EDD;/* 虧損：螢光紫 */
    --financial-none: #00F0FF;/* 平盤：電馭青 */

    /* 相容原本的變數名以確保排版不崩潰 */
    --cathay-green: var(--financial-up);
    --cathay-dark-green: #C91864; /* 較暗的粉紅 */
    --cathay-red: var(--financial-down);
    --cathay-yellow: var(--financial-none); 
    --cathay-bg-light: var(--bg-main);
    --cathay-white: var(--bg-card);
    --border-color: rgba(255, 42, 133, 0.2);  /* 亮粉紅微光邊框 */
    
    --shadow-soft: 0 8px 32px 0 rgba(255, 42, 133, 0.1); /* 柔和的粉色發光陰影 */
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

/* 頂部總資產 Header 樣式 (已改為深色專業風) */
.cathay-app-header {
    background-color: var(--bg-card);
    color: var(--text-primary);
    padding: 24px 20px;
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
    margin: -1rem -1rem 20px -1rem;
    box-shadow: var(--shadow-soft);
    text-align: center;
    border: 1px solid var(--border-color);
}
.cathay-app-header h1 {
    color: var(--text-primary) !important;
    font-size: 24px;
    margin: 0;
    font-weight: 700;
}
.cathay-app-header .total-value {
    font-size: 24px;
    font-weight: 700;
    margin-top: 8px;
    color: var(--text-primary);
}

/* 毛玻璃卡片 */
.card, [data-testid="metric-container"], .cathay-card {
    background-color: var(--cathay-white) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
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
.stButton>button[kind="primary"] {
    background-color: var(--cathay-green) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 600 !important;
    padding: 8px 24px !important;
    transition: background-color 0.2s ease;
}
.stButton>button[kind="primary"] * {
    color: white !important;
}
.stButton>button[kind="primary"]:hover {
    background-color: var(--cathay-dark-green) !important;
}

.stButton>button[kind="secondary"] {
    background-color: var(--bg-card) !important;
    color: var(--cathay-green) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 50px !important;
    font-weight: 600 !important;
    padding: 8px 24px !important;
    transition: all 0.2s ease;
}
.stButton>button[kind="secondary"] * {
    color: var(--cathay-green) !important;
}
.stButton>button[kind="secondary"]:hover {
    background-color: rgba(255, 255, 255, 0.05) !important;
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

/* 側邊欄導覽列：精簡垂直選單（方案一）*/
[data-testid="stSidebarNav"] ul {
    display: flex !important;
    flex-direction: column !important;
    gap: 2px !important;
    padding: 8px 4px !important;
}
[data-testid="stSidebarNav"] li {
    background-color: transparent !important;
    border-radius: 10px !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stSidebarNav"] a {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 10px 12px !important;
    background-color: transparent !important;
    gap: 10px !important;
    border-radius: 10px !important;
    border-left: 3px solid transparent !important;
    transition: background-color 0.15s ease !important;
}
[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(255, 255, 255, 0.05) !important;
}
/* 目前頁面：淡色底 + 左側色條標示，取代原本的九宮格外框 */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(0, 163, 82, 0.1) !important;
    border-left: 3px solid var(--cathay-green) !important;
    border-radius: 10px !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] span {
    color: var(--cathay-green) !important;
    font-weight: 700 !important;
}
[data-testid="stSidebarNav"] a > span:first-child { /* icon span */
    font-size: 20px !important;
    margin: 0 !important;
    line-height: 1 !important;
}
[data-testid="stSidebarNav"] a > span:last-child { /* text span */
    font-size: 14px !important;
    margin-top: 0 !important;
    text-align: left !important;
    white-space: nowrap !important;
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

/* DataFrame 表格優化 (HTML 表格渲染專用) */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    background-color: var(--bg-card);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 24px;
}
.custom-table th, .custom-table td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
    border-left: none;
    border-right: none;
    text-align: right; /* 數字欄位靠右對齊 */
    white-space: nowrap; /* 不允許截斷 */
}
.custom-table th {
    background-color: rgba(255,255,255,0.03);
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
}
.custom-table td {
    color: var(--text-primary);
}
.custom-table tbody tr:hover td {
    background-color: rgba(255,255,255,0.05);
}
/* 代號與券商保持靠左 */
.custom-table th:first-child, .custom-table td:first-child,
.custom-table th:last-child, .custom-table td:last-child {
    text-align: left;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border-color);
    background-color: var(--bg-card);
}

/* 徹底移除 Plotly 圖表外層的突兀外框與留白 */
[data-testid="stPlotlyChart"], 
[data-testid="stPlotlyChart"] > div, 
[data-testid="stPlotlyChart"] iframe {
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 0 !important;
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

/* 頁面標題區塊 */
.page-header {
    background: linear-gradient(90deg, rgba(0, 163, 82, 0.05) 0%, transparent 100%);
    border-left: 4px solid var(--cathay-green);
    padding: 12px 20px;
    border-radius: 0 12px 12px 0;
    margin-bottom: 24px;
}
.page-header h2 {
    margin: 0;
    color: var(--text-primary);
}
.page-header p {
    margin: 4px 0 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* 數據卡片 (Metric Card) */
.metric-card {
    background: var(--cathay-white);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 18px 22px;
    margin: 6px 0;
    box-shadow: var(--shadow-soft);
}



.custom-table th:first-child, .custom-table td:first-child {
    text-align: left; /* 第一欄 (代號) 靠左對齊 */
}

/* 配息時間軸 (Dividends Timeline) */
.timeline-container {
    background-color: var(--bg-card);
    border-radius: 12px;
    padding: 24px;
    box-shadow: var(--shadow-soft);
    border: 1px solid var(--border-color);
    max-height: 600px;
    overflow-y: auto;
}
/* 自訂捲軸 */
.timeline-container::-webkit-scrollbar {
    width: 6px;
}
.timeline-container::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 4px;
}
.timeline-item {
    position: relative;
    padding-left: 24px;
    padding-bottom: 16px;
    border-left: 2px solid #334155;
}
.timeline-item:last-child {
    border-left: 2px solid transparent;
    padding-bottom: 0;
}
.timeline-node {
    position: absolute;
    left: -7px;
    top: 6px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: var(--cathay-green);
    border: 2px solid var(--bg-card);
}
.timeline-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #334155;
    padding-bottom: 16px;
    margin-bottom: 4px;
}
.timeline-item:last-child .timeline-content {
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
}
.tl-left {
    display: flex;
    flex-direction: column;
    min-width: 80px;
}
.tl-symbol {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
}
.tl-type {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 2px;
}
.tl-middle {
    display: flex;
    flex-direction: column;
    color: #94a3b8;
    font-size: 13px;
    gap: 4px;
    flex-grow: 1;
    margin-left: 24px;
}
.tl-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
    min-width: 120px;
}
.tl-amount {
    font-size: 18px;
    font-weight: 700;
    color: #10b981;
}
.badge-status-done {
    background-color: #065f46;
    color: #34d399;
    padding: 4px 10px;
    border-radius: 50px;
    font-size: 11px;
    font-weight: 600;
}
.badge-status-pending {
    background-color: #78350f;
    color: #fbbf24;
    padding: 4px 10px;
    border-radius: 50px;
    font-size: 11px;
    font-weight: 600;
}

</style>""", unsafe_allow_html=True)

