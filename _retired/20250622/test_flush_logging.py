#!/usr/bin/env python3
"""
flush機能付きログ設定テストスクリプト

このスクリプトは、修正されたmain.pyと同じログ設定を使用して、
print()とapp.logger.info()が両方ともstdoutに出力されるかをテストします。
"""

import logging
import sys
from flask import Flask

def test_flush_logging():
    """flush機能付きログ設定をテスト"""
    print("🧪 flush機能付きログ設定テスト開始", flush=True)
    
    # setup_logging()と同じ設定
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True
    )
    
    root_handler = logging.StreamHandler(sys.stdout)
    root_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(root_handler)
    
    # 一時ファイル出力も併用（デバッグ用）
    file_handler = logging.FileHandler('test_app.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(file_handler)
    
    print(f"🔍 setup_logging() - root.handlers: {root_logger.handlers}", flush=True)
    print(f"🔍 setup_logging() - root.level: {root_logger.level}", flush=True)
    
    # Flaskアプリを作成
    app = Flask(__name__)
    
    # create_app()と同じ設定
    app_logger = logging.getLogger(app.name)
    app_logger.handlers.clear()
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    
    app_handler = logging.StreamHandler(sys.stdout)
    app_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    app_logger.addHandler(app_handler)
    
    # app.loggerにもファイル出力を追加（デバッグ用）
    app_file_handler = logging.FileHandler('test_app.log', mode='a', encoding='utf-8')
    app_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    app_logger.addHandler(app_file_handler)
    
    print(f"🔍 create_app() - app.name: {app.name}", flush=True)
    print(f"🔍 create_app() - app_logger.handlers: {app_logger.handlers}", flush=True)
    print(f"🔍 create_app() - app_logger.propagate: {app_logger.propagate}", flush=True)
    print(f"🔍 create_app() - app_logger.level: {app_logger.level}", flush=True)
    sys.stdout.flush()  # 強制フラッシュ
    
    # テストログ出力
    print("\n📝 テストログ出力:", flush=True)
    print("✅ print() - アクセス成功", flush=True)
    app.logger.info("🧪 app.logger.info() - アクセス成功")
    sys.stdout.flush()  # 強制フラッシュ
    
    print("\n✅ flush機能付きログ設定テスト完了", flush=True)

if __name__ == "__main__":
    test_flush_logging() 