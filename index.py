from custom_info import query_info
from entity.paperQuery import PaperQuery

# 查询条件
years = ["2025","2024"] # 支持多个年份查询
keywords = ["cluster", "contrastive"] # 支持多个关键词查询


# 创建查询对象并运行
paper_query = PaperQuery(query_info)
paper_query.run(years, keywords)