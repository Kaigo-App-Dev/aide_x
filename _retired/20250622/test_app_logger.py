#!/usr/bin/env python3
"""
app.logger設定テストスクリプト

このスクリプトは、main.pyと同じapp.logger設定を使用して、
アクセスログが正しく出力されるかをテストします。
"""

import logging
import sys
from flask import Flask

def test_app_logger():
    """app.loggerの設定をテスト"""
    print("🧪 app.logger設定テスト開始")
    
    # 既存の設定を完全クリア
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # 基本設定を強制的に適用
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True
    )
    
    # Flaskアプリを作成
    app = Flask(__name__)
    
    # Flaskアプリ作成後のログ設定（main.pyと同じ）
    app_logger = logging.getLogger(app.name)
    app_logger.handlers.clear()
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    
    # app.loggerに直接stdoutハンドラーを追加
    app_handler = logging.StreamHandler(sys.stdout)
    app_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    app_logger.addHandler(app_handler)
    
    # 設定確認
    print(f"🔍 app.name: {app.name}")
    print(f"🔍 app_logger.handlers: {app_logger.handlers}")
    print(f"🔍 app_logger.propagate: {app_logger.propagate}")
    print(f"🔍 app_logger.level: {app_logger.level}")
    
    # テストログ出力
    print("\n📝 テストログ出力:")
    
    # アクセスログのシミュレーション
    app.logger.info("[ACCESS] GET /log-test from 127.0.0.1")
    app.logger.info("[ACCESS] POST /api/test from 192.168.1.100")
    app.logger.info("[RESPONSE] GET /log-test -> 200")
    app.logger.info("[RESPONSE] POST /api/test -> 201")
    
    # その他のログ
    app.logger.info("🧪 app.logger - アクセス成功")
    
    print("\n✅ app.logger設定テスト完了")

if __name__ == "__main__":
    test_app_logger() 