import requests

# 代理设置
proxies = {
    'http': 'http://508144:a0ddcdf06@s2174.ips5.vip:9128',
    'https': 'http://508144:a0ddcdf06@s2174.ips5.vip:9128',
}

# 请求的 URL，直接拼接参数
url = 'https://api.getgrass.io/retrieveDevice?input=%7B%22deviceId%22%3A%2264eb65e0-8c62-55f0-a57c-4ef52cce6bef%22%7D'

# 请求头
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'authorization': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkJseGtPeW9QaWIwMlNzUlpGeHBaN2JlSzJOSEJBMSJ9.eyJ1c2VySWQiOiIyc2xFcE5XT25DVWdtYXZmdnNtc0t4WFdsdFEiLCJlbWFpbCI6Ijg3OTUwNDIyOEBxcS5jb20iLCJzY29wZSI6IlVTRVIiLCJpYXQiOjE3MzkzNDg2NDMsIm5iZiI6MTczOTM0ODY0MywiZXhwIjoxNzcwNDUyNjQzLCJhdWQiOiJ3eW5kLXVzZXJzIiwiaXNzIjoiaHR0cHM6Ly93eW5kLnMzLmFtYXpvbmF3cy5jb20vcHVibGljIn0.I1NNsTKYUhpFjp2BJIzNiTLQtJb6izsegcS5-0R2F0HhNSek1gyFkUippk47k40eNzYj4iB6RCEZKoAM93sNac7S8iOJ4YiOG-hX0v5Dpn8q_OpblxUIGrGkIMFGXfuA7z6a3pMidocc5moyD7F5tNlz447uTA_uuZZzY0bd10JSg-RoMkYVFOq3FL5ZdZd_4FT-s5MprPgB5ZwxR2GQxs87eh_zq5Z4tAMLwtZfHc7zZ6HfRkr0OnoS-hYnMy0Dk9_tlC2SJWEn8zU58bL6-GoBygw89uy38nMWdQW08tWYXASXpurLZl2gzno0Uvb24eNAGree3qS6xaG51KbHyQ',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'none',
    'sec-fetch-storage-access': 'active',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
}

print('开始请求')

# 发送请求
response = requests.get(url, headers=headers, proxies=proxies)

# 打印响应内容
print(response.json())
