import json

# 读取用户 ID
with open('userid.txt', 'r') as user_file:
    user_ids = [line.strip() for line in user_file.readlines()]

# 读取代理
with open('proxy.txt', 'r') as proxy_file:
    proxies = [line.strip() for line in proxy_file.readlines()]

num_proxies = int(input("请输入每个用户 ID 需要的代理数量: "))

# 检查是否有足够的代理
total_proxies_needed = len(user_ids) * num_proxies
if total_proxies_needed > len(proxies):
    print(f"错误：代理数量不足！需要 {total_proxies_needed} 个代理，但只有 {len(proxies)} 个代理。")
    exit()

# 创建一个字典来存储用户与代理的映射
user_proxy_mapping = {}

# 计算每个用户应该获得的代理的起始索引
for i, user_id in enumerate(user_ids):
    start_index = i * num_proxies  # 每个用户的起始索引
    end_index = start_index + num_proxies  # 每个用户的结束索引
    user_proxy_mapping[user_id] = proxies[start_index:end_index]

# 将结果写入 user_proxy_mapping.json 文件
with open('user_proxy_mapping.json', 'w') as json_file:
    json.dump(user_proxy_mapping, json_file, indent=4)

print("user_proxy_mapping.json 文件已生成。")