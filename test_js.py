import requests
import re

url = "https://finance.vietstock.vn/FPT/tin-tuc-su-kien.htm"
html = requests.get(url).text
js_links = re.findall(r'<script\s+src="([^"]+)"', html)

for js in js_links:
    if "vietstock" in js or js.startswith("/"):
        js_url = f"https://finance.vietstock.vn{js}" if js.startswith("/") else js
        print(f"Checking {js_url}")
        js_content = requests.get(js_url).text
        apis = re.findall(r'url:\s*["\']([^"\']+)["\']', js_content)
        if apis:
            print("Found APIs:", set(apis))
