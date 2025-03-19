import uuid
import json
import random
import mmh3  

REACT_APP_NAMESPACE =  "bed9e870-4e94-4260-a1fa-815514adfce1"

def get_random_macos_version():
    versions = [
        {"version": "10_15_7", "name": "Catalina", "weight": 0.3},
        {"version": "10_15_6", "name": "Catalina", "weight": 0.1},
        {"version": "10_14_6", "name": "Mojave", "weight": 0.1},
        {"version": "10_13_6", "name": "High Sierra", "weight": 0.05},
        {"version": "13_6_3", "name": "Ventura", "weight": 0.15},
        {"version": "14_1_1", "name": "Sonoma", "weight": 0.2},
        {"version": "14_1_2", "name": "Sonoma", "weight": 0.1},
    ]

    random_num = random.random()
    current_weight = 0

    for ver in versions:
        current_weight += ver["weight"]
        if random_num <= current_weight:
            return ver["version"]

    return "14_1_2"

def generate_random_fingerprint():
    def get_random_browser_profile():
        chrome_versions = [
            "131.0.6778.86",
            "129.0.6668.101",
            "129.0.6668.71",
            "128.0.6613.138",
            "130.0.6723.70",
        ]

        platforms = {
            "Windows": {
                "name": "Win32",
                "ua": "Windows NT 10.0; Win64; x64",
                "weight": 0.6,
            },
            "Mac": {
                "name": "MacIntel",
                "ua": f"Macintosh; Intel Mac OS X {get_random_macos_version()}",
                "weight": 0.4,
            },
        }

        resolutions = [
            {"res": [1920, 1080], "weight": 0.4},
            {"res": [2560, 1440], "weight": 0.2},
            {"res": [1366, 768], "weight": 0.15},
            {"res": [1440, 900], "weight": 0.15},
            {"res": [3840, 2160], "weight": 0.1},
        ]

        platform = platforms["Windows"] if random.random() < platforms["Windows"]["weight"] else platforms["Mac"]

        # 选择分辨率
        random_res = random.random()
        current_weight = 0
        selected_resolution = resolutions[-1]["res"]  # 默认值
        for res in resolutions:
            current_weight += res["weight"]
            if random_res <= current_weight:
                selected_resolution = res["res"]
                break

        languages = [
            {"lang": "en-US", "weight": 0.4},
            {"lang": "zh-CN", "weight": 0.4},
            {"lang": "en-GB", "weight": 0.1},
            {"lang": "zh-TW", "weight": 0.1},
        ]

        # 选择语言
        random_res = random.random()
        current_weight = 0
        selected_language = languages[0]["lang"]  # 默认值
        for lang in languages:
            current_weight += lang["weight"]
            if random_res <= current_weight:
                selected_language = lang["lang"]
                break

        return {
            "userAgent": f"Mozilla/5.0 ({platform['ua']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
            "language": selected_language,
            "platform": platform["name"],
            "colorDepth": 24 if platform["name"] == "Win32" else 30,
            "screenResolution": selected_resolution,
            "hardwareConcurrency": random.choice([4, 6, 8, 12, 16]) if platform["name"] == "Win32" else random.choice([8, 10, 12]),
            "deviceMemory": random.choice([4, 8, 16, 32]) if platform["name"] == "Win32" else random.choice([8, 16, 32]),
            "timezoneOffset": random.choice([480, -420, -480]),
            "hasCanvas": True,
            "hasWebGL": True,
            "hasCookies": True,
            "hasLocalStorage": True,
            "hasSessionStorage": True,
            "pluginsCount": 2 + random.randint(0, 3),
        }

    profile = get_random_browser_profile()
    components = "###".join([
        str(x) for x in [
            profile["userAgent"],
            profile["language"],
            profile["colorDepth"],
            "x".join(map(str, profile["screenResolution"])),
            profile["timezoneOffset"],
            profile["platform"],
            profile["hardwareConcurrency"],
            profile["deviceMemory"],
            profile["pluginsCount"],
            profile["hasCanvas"],
            profile["hasWebGL"],
            profile["hasCookies"],
            profile["hasLocalStorage"],
            profile["hasSessionStorage"],
        ]
    ])

    # 生成 MurmurHash
    hash_value = mmh3.hash(components, 31)
    fingerprint_hash = str(100000000 + (abs(hash_value) % 900000000))

    return {
        "hash": fingerprint_hash,
        "userAgent": profile["userAgent"]
    }


def generate_config():
    try:
        # 修改：读取所有用户ID
        with open('user_proxy_mapping.json', 'r', encoding='utf-8') as f:
            user_proxy_mapping = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError('未找到 user_proxy_mapping.json 文件')

    config = []
    # 遍历每个用户及其代理
    for user_id, proxies in user_proxy_mapping.items():
        for proxy in proxies:
            fingerprint = generate_random_fingerprint()
            browser_id = str(uuid.uuid5(uuid.UUID(REACT_APP_NAMESPACE), fingerprint["hash"]))
            config.append({
                "user_id": user_id,
                "browser_id": browser_id,
                "user_agent": fingerprint["userAgent"],
                "proxy": proxy
            })

    # 将配置写入config.py文件
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write('CONFIG = ' + json.dumps(config, ensure_ascii=False, indent=2))

    return config

if __name__ == '__main__':
    generate_config()
   