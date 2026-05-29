"""頁面1：持倉總覽（雙語 + Supabase Auth）"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import get_all_transactions, get_price_cache
from portfolio import compute_holdings, compute_portfolio_with_prices

st.set_page_config(page_title=f"VN Portfolio | {t('portfolio_title')}", page_icon="💼", layout="wide")

from theme import load_css
load_css()

