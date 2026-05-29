"""頁面2：交易記錄（雙語 + db_router）"""
import streamlit as st
import pandas as pd
from datetime import date
from i18n import t, render_lang_switcher
from auth_page import check_auth, render_user_info_sidebar
from db_router import (add_transaction, delete_transaction,
                        get_all_transactions, import_transactions_from_csv)
from config import BROKERS

st.set_page_config(page_title=f"VN Portfolio | {t('transactions_title')}", page_icon="📝", layout="wide")

from theme import load_css
load_css()
