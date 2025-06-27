#!/usr/bin/env python3
"""
簡素化されたログ設定テストスクリプト

このスクリプトは、修正されたmain.pyと同じログ設定を使用して、
print()とapp.logger.info()が両方ともstdoutに出力されるかをテストします。
"""

import logging
import sys
from flask import Flask

def test_simplified_logging():
    """簡素化されたログ設定をテスト"""
    print("🧪 簡素化されたログ設定テスト開始")
    
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
    
    print(f"🔍 setup_logging() - root.handlers: {root_logger.handlers}")
    print(f"🔍 setup_logging() - root.level: {root_logger.level}")
    
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
    
    print(f"🔍 create_app() - app.name: {app.name}")
    print(f"🔍 create_app() - app_logger.handlers: {app_logger.handlers}")
    print(f"🔍 create_app() - app_logger.propagate: {app_logger.propagate}")
    print(f"🔍 create_app() - app_logger.level: {app_logger.level}")
    
    # テストログ出力
    print("\n📝 テストログ出力:")
    print("✅ print() - アクセス成功")
    app.logger.info("🧪 app.logger.info() - アクセス成功")
    
    print("\n✅ 簡素化されたログ設定テスト完了")

if __name__ == "__main__":
    test_simplified_logging() 