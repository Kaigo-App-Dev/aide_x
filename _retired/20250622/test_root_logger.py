#!/usr/bin/env python3
"""
ルートロガーテストスクリプト

このスクリプトは、修正されたmain.pyと同じログ設定を使用して、
print()とlogging.getLogger("root").info()が両方ともstdoutに出力されるかをテストします。
"""

import logging
import sys
from flask import Flask

def test_root_logger():
    """ルートロガー設定をテスト"""
    print("🧪 ルートロガー設定テスト開始", flush=True)
    
    # setup_logging()と同じ設定
    import logging, sys
    
    # ルートロガー（logging.getLogger("root")）を使って一元出力
    root_logger = logging.getLogger("root")
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    # stdoutハンドラーを追加
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # 一時ファイル出力も併用（デバッグ用）
    file_handler = logging.FileHandler('test_root.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    print(f"🔍 setup_logging() - root.handlers: {root_logger.handlers}", flush=True)
    print(f"🔍 setup_logging() - root.level: {root_logger.level}", flush=True)
    
    # テストログ出力
    print("\n📝 テストログ出力:", flush=True)
    print("✅ print() - アクセス成功", flush=True)
    root_logger.info("🧪 logger(root) - アクセス成功")
    
    # アクセスログのシミュレーション
    root_logger.info("[ACCESS] GET /log-test from 127.0.0.1")
    root_logger.info("[RESPONSE] GET /log-test -> 200")
    
    print("\n✅ ルートロガー設定テスト完了", flush=True)

if __name__ == "__main__":
    test_root_logger() 