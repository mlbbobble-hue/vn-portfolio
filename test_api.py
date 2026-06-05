import requests
import json

url = "https://finance.vietstock.vn/data/corporateevents"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest"
}
data = {
    "Code": "FPT",
    "Type": "0",
    "OrderBy": "Time",
    "OrderDirection": "desc",
    "Page": "1",
    "PageSize": "5"
}

try:
    res = requests.post(url, headers=headers, data=data)
    print(res.status_code)
    print(res.text[:500])
except Exception as e:
    print(e)

