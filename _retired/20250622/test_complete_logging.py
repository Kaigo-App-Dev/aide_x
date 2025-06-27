#!/usr/bin/env python3
"""
完全なログ設定テストスクリプト

このスクリプトは、修正されたmain.pyと同じログ設定を使用して、
print()とapp.logger.info()が両方ともstdoutに出力されるかをテストします。
"""

import logging
import sys
from flask import Flask

def test_complete_logging():
    """完全なログ設定をテスト"""
    print("🧪 完全なログ設定テスト開始", flush=True)
    
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
    
    # werkzeugロガーも明示的に設定
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = False
    
    werkzeug_handler = logging.StreamHandler(sys.stdout)
    werkzeug_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    werkzeug_logger.addHandler(werkzeug_handler)
    
    # 一時ファイル出力も併用（デバッグ用）
    file_handler = logging.FileHandler('test_complete.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(file_handler)
    
    werkzeug_file_handler = logging.FileHandler('test_complete.log', mode='a', encoding='utf-8')
    werkzeug_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    werkzeug_logger.addHandler(werkzeug_file_handler)
    
    print(f"🔍 setup_logging() - root.handlers: {root_logger.handlers}", flush=True)
    print(f"🔍 setup_logging() - werkzeug.handlers: {werkzeug_logger.handlers}", flush=True)
    
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
    
    app_file_handler = logging.FileHandler('test_complete.log', mode='a', encoding='utf-8')
    app_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    app_logger.addHandler(app_file_handler)
    
    # Flaskアプリ作成後にwerkzeugロガーを再設定
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = False
    
    werkzeug_handler = logging.StreamHandler(sys.stdout)
    werkzeug_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    werkzeug_logger.addHandler(werkzeug_handler)
    
    werkzeug_file_handler = logging.FileHandler('test_complete.log', mode='a', encoding='utf-8')
    werkzeug_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    werkzeug_logger.addHandler(werkzeug_file_handler)
    
    print(f"🔍 create_app() - app.name: {app.name}", flush=True)
    print(f"🔍 create_app() - app_logger.handlers: {app_logger.handlers}", flush=True)
    print(f"🔍 create_app() - werkzeug.handlers: {werkzeug_logger.handlers}", flush=True)
    sys.stdout.flush()
    
    # テストログ出力
    print("\n📝 テストログ出力:", flush=True)
    print("✅ print() - アクセス成功", flush=True)
    print(f"🔍 /log-test - app.name: {app.name}", flush=True)
    print(f"🔍 /log-test - app.logger.handlers: {app.logger.handlers}", flush=True)
    
    app.logger.info("🧪 app.logger.info() - アクセス成功")
    werkzeug_logger.info("🧪 werkzeug.logger.info() - アクセス成功")
    sys.stdout.flush()
    
    print("\n✅ 完全なログ設定テスト完了", flush=True)

if __name__ == "__main__":
    test_complete_logging() 