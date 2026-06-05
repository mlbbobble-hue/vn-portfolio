from playwright.sync_api import sync_playwright

def get_news(symbol):
    url = f"https://finance.vietstock.vn/{symbol}/tin-tuc-su-kien.htm"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        articles = page.query_selector_all("div.single_news, article, h3 a, h4 a, .news-title a, a.title-link")
        print(f"Found {len(articles)} potential news links")
        
        for a in articles[:10]:
            title = a.inner_text().strip()
            link = a.get_attribute("href")
            # Filter valid titles
            if title and len(title) > 20 and not "\n" in title:
                print(f"[{title}]({link})")
        
        browser.close()

if __name__ == "__main__":
    get_news("FPT")
