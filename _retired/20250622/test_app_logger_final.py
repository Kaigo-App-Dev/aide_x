#!/usr/bin/env python3
"""
最終的なapp.logger設定テストスクリプト

このスクリプトは、main.pyと同じapp.logger設定を使用して、
print()とapp.logger.info()が両方ともstdoutに出力されるかをテストします。
"""

import logging
import sys
from flask import Flask

def test_app_logger_final():
    """最終的なapp.logger設定をテスト"""
    print("🧪 最終的なapp.logger設定テスト開始")
    
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
    
    # root_loggerに明示的にstdoutハンドラーを追加
    root_handler = logging.StreamHandler(sys.stdout)
    root_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(root_handler)
    
    # werkzeugロガーの明示的設定
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = False  # 重複を避けるためFalseに設定
    
    # werkzeugロガーにも明示的にstdoutハンドラーを追加
    werkzeug_handler = logging.StreamHandler(sys.stdout)
    werkzeug_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    werkzeug_logger.addHandler(werkzeug_handler)
    
    # Flaskアプリを作成
    app = Flask(__name__)
    
    # Flaskアプリ作成後のログ設定（main.pyと同じ）
    app_logger = logging.getLogger(app.name)
    app_logger.handlers.clear()
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False  # 重複を避けるためFalseに設定
    
    # app.loggerに直接stdoutハンドラーを追加
    app_handler = logging.StreamHandler(sys.stdout)
    app_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    app_logger.addHandler(app_handler)
    
    # app.logger設定の確認
    print(f"🔍 app.name: {app.name}")
    print(f"🔍 app_logger.handlers: {app_logger.handlers}")
    print(f"🔍 app_logger.propagate: {app_logger.propagate}")
    print(f"🔍 app_logger.level: {app_logger.level}")
    
    # テストログ出力
    print("\n📝 テストログ出力:")
    
    # print()のテスト
    print("✅ print() - アクセス成功")
    
    # app.loggerのテスト
    app.logger.info("🧪 app.logger.info() - アクセス成功")
    
    # アクセスログのシミュレーション
    app.logger.info("[ACCESS] GET /log-test from 127.0.0.1")
    
    print("\n✅ 最終的なapp.logger設定テスト完了")

if __name__ == "__main__":
    test_app_logger_final() 