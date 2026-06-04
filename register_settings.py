import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """watchlist_page = st.Page("views/04_watchlist.py", title=t("nav_watchlist"), icon=":material/notifications_active:")"""
new1 = """watchlist_page = st.Page("views/04_watchlist.py", title=t("nav_watchlist"), icon=":material/notifications_active:")
settings_page = st.Page("views/05_settings.py", title=t("nav_settings"), icon=":material/settings:")"""

target2 = """nav_pages = [dashboard_page, portfolio_page, transactions_page, dividends_page, watchlist_page]"""
new2 = """nav_pages = [dashboard_page, portfolio_page, transactions_page, dividends_page, watchlist_page, settings_page]"""

if target1 in content and target2 in content:
    content = content.replace(target1, new1)
    content = content.replace(target2, new2)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Registered settings page in app.py")
else:
    print("Targets not found in app.py")
