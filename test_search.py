import requests

url = "https://vietstock.vn/News/Search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "keyword": "FPT",
    "page": 1,
    "pageSize": 5
}
try:
    res = requests.post(url, headers=headers, data=data)
    print(res.status_code)
    print(res.text[:500])
except Exception as e:
    print(e)
