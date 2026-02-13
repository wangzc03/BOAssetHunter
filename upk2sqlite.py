#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
# @Author  : wangzc
# @Date    : 2026/2/13 12:25
# @File    : upk2sqlite.py
# @Description: 
"""
import os
import subprocess
import sqlite3
import re

# --- config ---
UMODEL_PATH = r"C:\Users\wangzc\Downloads\umodel_win32\umodel.exe"  # umodel
GAME_DATA_PATH = r"D:\workplace\2026\bo-upk"  # UPK
DB_NAME = "game_assets_test.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 创建表结构
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package TEXT,      -- UPK包名
            asset_type TEXT,   -- type (StaticMesh/Material等)
            asset_name TEXT,   -- 资产实际名称
            raw_line TEXT      -- 原始数据备查
        )
    ''')
    conn.commit()
    return conn


def parse_and_save(package_name, stdout_text, conn):
    cursor = conn.cursor()
    # 正则表达式说明：
    # \s+(\d+)\s+      -> 匹配开头的序号和空白
    # [0-9A-F]+\s+     -> 匹配十六进制地址
    # [0-9A-F]+\s+     -> 匹配大小
    # ([a-zA-Z0-9_]+)\s+ -> 捕获组1：类型 (asset_type)
    # ([a-zA-Z0-9_]+)  -> 捕获组2：名字 (asset_name)
    pattern = re.compile(r'\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+)')

    entries = []
    for line in stdout_text.splitlines():
        match = pattern.search(line)
        if match:
            a_type = match.group(1)
            a_name = match.group(2)

            # 过滤掉不需要的类型 (比如 Package, RB_BodySetup 等)
            if a_type in ['StaticMesh', 'Material', 'MaterialInstanceConstant', 'Texture2D']:
                entries.append((package_name, a_type, a_name, line.strip()))

    if entries:
        cursor.executemany('INSERT INTO assets (package, asset_type, asset_name, raw_line) VALUES (?, ?, ?, ?)',
                           entries)
        conn.commit()
        print(f"  [+] 已存入 {len(entries)} 条资产信息")


def main():
    if not os.path.exists(UMODEL_PATH):
        print("错误：找不到 umodel.exe，请检查路径。")
        return

    conn = init_db()

    # 遍历文件夹下所有 .upk
    upk_files = [f for f in os.listdir(GAME_DATA_PATH) if f.endswith('.upk')]
    print(f"找到 {len(upk_files)} 个 UPK 文件，准备扫描...")

    for upk in upk_files:
        upk_path = os.path.join(GAME_DATA_PATH, upk)
        print(f"正在扫描包: {upk}")

        try:
            # 执行命令行
            result = subprocess.run(
                [UMODEL_PATH, "-path=" + GAME_DATA_PATH, "-list", upk],
                capture_output=True,
                text=True,
                encoding='utf-8',  # 如果报错尝试 'gbk'
                errors='ignore'
            )

            if result.stdout:
                parse_and_save(upk, result.stdout, conn)

        except Exception as e:
            print(f"  [!] 扫描 {upk} 时出错: {e}")

    conn.close()
    print("\n扫描完成！所有数据已写入 " + DB_NAME)


if __name__ == "__main__":
    main()