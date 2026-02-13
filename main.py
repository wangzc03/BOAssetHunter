#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
# @Author  : wangzc
# @Date    : 2026/2/13 13:36
# @File    : main.py
# @Description: 
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from bo_search_engine import BOSearchEngine

app = FastAPI()
engine = BOSearchEngine()
engine.load_index() # 确保索引已存在

# 允许跨域，方便 HTML 直接调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
async def api_search(
    q: str,
    pkg: str = None,
    type: str = None,
    limit: int = 10
):
    results = engine.search(q, filter_package=pkg, filter_type=type, top_k=limit)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)