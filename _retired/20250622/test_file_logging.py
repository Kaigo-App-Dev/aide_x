#!/usr/bin/env python3
"""
ファイル出力ログ設定テストスクリプト

このスクリプトは、修正されたmain.pyと同じログ設定を使用して、
ファイル出力を標準としたログ設定をテストします。
"""

import logging
import sys
from flask import Flask

def test_file_logging():
    """ファイル出力ログ設定をテスト"""
    # 開発モード設定
    FLASK_DEBUG = False
    
    # setup_logging()と同じ設定
    import logging, sys
    
    # ルートロガー（logging.getLogger("root")）を使って一元出力
    root_logger = logging.getLogger("root")
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    # ファイルハンドラーを標準として追加
    file_handler = logging.FileHandler('test_file.log', mode='w', encoding='utf-8')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 開発モード時のみstdoutハンドラーを追加
    if FLASK_DEBUG:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        root_logger.addHandler(stdout_handler)
    
    # デバッグ用：設定確認
    root_logger.info(f"🔍 setup_logging() - root.handlers: {root_logger.handlers}")
    root_logger.info(f"🔍 setup_logging() - root.level: {root_logger.level}")
    root_logger.info(f"🔍 setup_logging() - FLASK_DEBUG: {FLASK_DEBUG}")
    
    # テストログ出力
    root_logger.info("🧪 setup_logging() 完了 - ログ設定テスト")
    root_logger.info("✅ /log-test - アクセス成功")
    root_logger.info("🧪 logger(root) - アクセス成功")
    
    # アクセスログのシミュレーション
    root_logger.info("[ACCESS] GET /log-test from 127.0.0.1")
    root_logger.info("[RESPONSE] GET /log-test -> 200")
    
    print("✅ ファイル出力ログ設定テスト完了")
    print("📄 ログファイル: test_file.log を確認してください")

if __name__ == "__main__":
    test_file_logging() 