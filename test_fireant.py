import requests
url = "https://restv2.fireant.vn/symbols/FPT/news?offset=0&limit=5"
try:
    res = requests.get(url, timeout=5)
    print(res.status_code)
    print(res.json()[:2])
except Exception as e:
    print(e)
