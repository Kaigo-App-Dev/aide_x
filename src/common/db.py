"""
データベース接続管理モジュール
"""
import sqlite3
from flask import g

DATABASE = "your_database_file.db"  # 例：data/structure.db など

def get_db():
    """データベース接続を取得"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db 