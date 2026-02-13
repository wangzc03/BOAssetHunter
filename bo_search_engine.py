#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
# @Author  : wangzc
# @Date    : 2026/2/13 12:58
# @File    : bo_search_engine.py
# @Description: 
"""
import sqlite3
import os
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util

# --- 配置 ---
DB_NAME = "game_assets_test.db"
VECTOR_CACHE = "assets_vectors.npy"
ID_CACHE = "assets_ids.npy"
# 推荐模型：多语言支持，体积小（约400MB），CPU运行极快
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'


class BOSearchEngine:
    def __init__(self):
        print(f"正在加载 AI 模型 ({MODEL_NAME})...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.embeddings = None
        self.asset_ids = None

    def build_index(self):
        """读取数据库并生成向量库"""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, asset_name, asset_type FROM assets")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("数据库中没有数据，请先运行 upk2sqlite.py")
            return

        # 预处理文本：StaticMesh Fuel_Drum -> "StaticMesh Fuel Drum"
        # 替换下划线为空格有助于模型更好地识别单词含义
        texts = [f"{r[2]} {r[1].replace('_', ' ')}" for r in rows]
        ids = [r[0] for r in rows]

        print(f"正在对 {len(texts)} 个资产进行向量化，请稍候...")
        self.embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        self.asset_ids = np.array(ids)

        # 保存到本地，下次启动秒开
        np.save(VECTOR_CACHE, self.embeddings)
        np.save(ID_CACHE, self.asset_ids)
        print(f"索引构建完成，已保存至 {VECTOR_CACHE}")

    def load_index(self):
        """从本地加载向量索引"""
        if os.path.exists(VECTOR_CACHE) and os.path.exists(ID_CACHE):
            self.embeddings = np.load(VECTOR_CACHE)
            self.asset_ids = np.load(ID_CACHE)
            print("已从本地缓存加载向量索引。")
            return True
        return False

    def search(self, query, filter_package=None, filter_type=None, top_k=5):
        """语义搜索核心函数"""
        if self.embeddings is None:
            if not self.load_index():
                print("未找到索引文件，请先运行 build_index()")
                return []

        # 1. 编码查询词
        query_vec = self.model.encode(query, convert_to_tensor=True)

        # 2. 计算余弦相似度
        cos_scores = util.cos_sim(query_vec, torch.from_numpy(self.embeddings))[0]

        # 3. 排序获取候选
        # 为了配合后面的“硬过滤”，我们先取稍多一点的候选（如 100 个）
        top_results = torch.topk(cos_scores, k=min(100, len(self.asset_ids)))

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        final_results = []

        for score, idx in zip(top_results[0], top_results[1]):
            db_id = int(self.asset_ids[idx])

            # 构建带过滤条件的 SQL
            sql = "SELECT package, asset_type, asset_name FROM assets WHERE id = ?"
            params = [db_id]

            if filter_package:
                sql += " AND package = ?"
                params.append(filter_package)
            if filter_type:
                sql += " AND asset_type = ?"
                params.append(filter_type)

            cursor.execute(sql, params)
            match = cursor.fetchone()

            if match:
                final_results.append({
                    "package": match[0],
                    "type": match[1],
                    "name": match[2],
                    "score": float(score)
                })

            if len(final_results) >= top_k:
                break

        conn.close()
        return final_results


# --- 使用示例 ---
if __name__ == "__main__":
    engine = BOSearchEngine()

    # 如果是第一次运行，或者数据库更新了，取消下面这一行的注释
    engine.build_index()

    while True:
        print("\n" + "=" * 50)
        q = input("请输入搜索词 (例如: '蓝色的桶' 或 '铁轨') [输入 q 退出]: ")
        if q.lower() == 'q':
            break

        # 示例：搜索并过滤
        results = engine.search(q, top_k=5)

        if not results:
            print("没有找到匹配的结果。")
        for i, res in enumerate(results):
            print(f"{i + 1}. [{res['type']}] {res['name']}")
            print(f"   库: {res['package']} | 相似度: {res['score']:.2f}")