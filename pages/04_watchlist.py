"""頁面4：觀察清單（雙語 + db_router）"""
import streamlit as st
import pandas as pd
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (get_watchlist, upsert_watchlist, delete_watchlist,
                        save_notification_settings, load_notification_settings,
                        get_price_cache, upsert_price_cache)
from market_data import get_stock_price, get_moving_average
from alerts import test_notification, check_and_fire_alerts
from portfolio import get_estimated_yield, get_dividend_income_summary

st.set_page_config(page_title=f"VN Portfolio | {t('watchlist_title')}", page_icon="🔔", layout="wide")

from theme import load_css
load_css()
