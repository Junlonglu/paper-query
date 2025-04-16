# 定义类型常量
VENUE_TYPES = {
    "journal": "期刊",
    "conference": "会议",
    # 可以在此扩展更多类型
}

# 可根据需求扩展，添加多个 venue（期刊或会议）
venues = [
    {
      "key": "AAAI",
      "full_name": "AAAI Conference on Artificial Intelligence",
      "type": "conference",  # 使用字符串表示类型
      "rank":"A",
      "url": "http://dblp.uni-trier.de/db/conf/aaai/"
    },
]