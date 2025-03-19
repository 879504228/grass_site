import requests
import json
from config import CONFIG

def call_api(user_config):
    url = 'https://director.getgrass.io/checkin'
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'User-Agent': user_config['user_agent']
    }
    data = {
        "browserId": user_config['browser_id'],
        "userId": user_config['user_id'],
        "version": "5.0.0",
        "extensionId": "ilehaonighjijnmpnagapkhpcdbhclfg",
        "userAgent": user_config['user_agent'],
        "deviceType": "extension"
    }
    
    # 使用代理
    proxy_parts = user_config['proxy'].split(':')
    print(proxy_parts)
    host = proxy_parts[0]
    port = proxy_parts[1]
    username = proxy_parts[2]
    password = proxy_parts[3]
    
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 检查请求是否成功
        # print('请求的结果是：', response.json())
        json_response = response.json()  # 获取 JSON 数据
        result = f"ws://{json_response['destinations'][0]}/?token={json_response['token']}"
        print('请求的结果是：', result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error for User ID {user_config['user_id']}: {e}")
        return None

def main():
    for user_config in CONFIG:
        result = call_api(user_config)
        if result is not None:
            print(f"User ID: {user_config['user_id']}, Result: {result}")

if __name__ == "__main__":
    main()
