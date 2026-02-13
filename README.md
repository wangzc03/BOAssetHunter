# RO2-Asset-Hunter
This is an RS2/RO2/BO asset finder based on AI-Embedding. You simply input what you want (e.g., "jungle leaves," "rusty iron gate"), and the AI ​​will immediately tell you which UPK package it's in and its name. By quickly finding assets through descriptive features, it significantly improves map creation efficiency.


# 解析 (Parser): UPK文件 -> 提取文本信息

# 存储 (Storage): 文本信息 -> SQLite

# 向量化 (Embedding): 文本清洗 -> 多语言模型 -> 向量库

# 查询 (Query): 用户中文输入 -> 向量化 -> 匹配最接近的资产