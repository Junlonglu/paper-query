import json
import os

# 导入要查询的期刊或会议信息
json_dir = os.path.dirname(__file__)
json_name = "default.json"  # 这里是你要查询的 JSON 文
with open(os.path.join(json_dir, json_name), 'r', encoding='utf-8') as file:
  query_info = json.load(file)

print(f"✅ 成功加载查询信息：{json_name}\n")
# print(f"🔍 查询信息：{query_info}")