"""頁面5：損益分析（雙語 + db_router）"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import get_all_transactions, get_dividend_events
from portfolio import compute_portfolio_with_prices, compute_holdings
from market_data import get_historical_prices

st.set_page_config(page_title=f"VN Portfolio | {t('analytics_title')}", page_icon="📉", layout="wide")

from theme import load_css
load_css()
