#!/usr/bin/env python3
"""
ログ設定テストスクリプト

このスクリプトは、main.pyと同じログ設定を使用して、
werkzeugロガーが正しく動作するかをテストします。
"""

import logging
import sys

def test_logging_setup():
    """main.pyと同じログ設定をテスト"""
    print("🧪 ログ設定テスト開始")
    
    # 既存の設定を完全クリア
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    print(f"🔍 クリア後 - root.handlers: {root_logger.handlers}")
    print(f"🔍 クリア後 - root.level: {root_logger.level}")
    
    # 基本設定を強制的に適用
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True
    )
    
    print(f"🔍 basicConfig後 - root.handlers: {root_logger.handlers}")
    print(f"🔍 basicConfig後 - root.level: {root_logger.level}")
    
    # werkzeugロガーの明示的設定
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = True
    
    # 設定確認
    print(f"🔍 werkzeug.handlers: {werkzeug_logger.handlers}")
    print(f"🔍 werkzeug.propagate: {werkzeug_logger.propagate}")
    print(f"🔍 werkzeug.level: {werkzeug_logger.level}")
    print(f"🔍 werkzeug.disabled: {werkzeug_logger.disabled}")
    
    # テストログ出力
    print("\n📝 テストログ出力:")
    
    # 直接printで確認
    print("✅ print() - 直接出力テスト")
    
    # rootロガーでテスト
    root_logger.info("🧪 root logger - アクセス成功")
    
    # werkzeugロガーでテスト
    werkzeug_logger.info("127.0.0.1 - - [19/Jun/2025 12:34:56] \"GET /log-test HTTP/1.1\" 200 -")
    werkzeug_logger.info("127.0.0.1 - - [19/Jun/2025 12:34:57] \"POST /api/test HTTP/1.1\" 201 -")
    
    # 他のロガーもテスト
    test_logger = logging.getLogger("test")
    test_logger.info("🧪 test logger - アクセス成功")
    
    app_logger = logging.getLogger("app")
    app_logger.info("🧪 app logger - アクセス成功")
    
    print("\n✅ ログ設定テスト完了")

if __name__ == "__main__":
    test_logging_setup() 