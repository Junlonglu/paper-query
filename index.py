from entity.paperQuery import PaperQuery

# 查询条件
years = ["2024"] # 支持多个年份查询
keywords = ["Speech"] # 支持多个关键词查询

# 创建查询对象并运行
paper_query = PaperQuery()
paper_query.run(years, keywords)