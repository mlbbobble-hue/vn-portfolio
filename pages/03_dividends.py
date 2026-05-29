"""頁面3：配息追蹤（雙語 + db_router）"""
import streamlit as st
import pandas as pd
from datetime import date
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (add_dividend_event, get_dividend_events, delete_dividend_event,
                        mark_dividend_applied, upsert_dividend_events_bulk,
                        get_portfolio_symbols, add_transaction)
from market_data import get_dividend_history
from portfolio import apply_stock_dividend, compute_holdings

st.set_page_config(page_title=f"VN Portfolio | {t('dividends_title')}", page_icon="💰", layout="wide")

from theme import load_css
load_css()
