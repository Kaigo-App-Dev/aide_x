#!/usr/bin/env python3
"""
E2Eテスト実行スクリプト

このスクリプトは、E2Eテストを簡単に実行するためのラッパーです。
"""

import sys
import os
import subprocess
import time
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def check_app_running():
    """アプリケーションが起動しているかチェック"""
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=5)
        return response.status_code == 200
    except:
        return False

def install_dependencies():
    """依存関係をインストール"""
    logger.info("📦 依存関係をインストール中...")
    
    try:
        # Playwrightのインストール
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "playwright>=1.40.0", "pytest-playwright>=0.4.0"
        ], check=True)
        
        # Playwrightブラウザのインストール
        subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], check=True)
        
        logger.info("✅ 依存関係のインストール完了")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 依存関係のインストールに失敗: {e}")
        return False

def run_e2e_tests():
    """E2Eテストを実行"""
    logger.info("🚀 E2Eテスト実行開始")
    
    try:
        # テストファイルのパス
        test_file = Path(__file__).parent / "test_structure_flow.py"
        
        # テスト実行
        result = subprocess.run([
            sys.executable, str(test_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ E2Eテスト成功")
            return True
        else:
            logger.error(f"❌ E2Eテスト失敗: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ E2Eテスト実行エラー: {e}")
        return False

def main():
    """メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🎯 E2Eテスト実行スクリプト開始")
    
    # 1. アプリケーションの起動確認
    logger.info("🔍 アプリケーションの起動確認中...")
    if not check_app_running():
        logger.error("❌ アプリケーションが起動していません")
        logger.info("💡 以下のコマンドでアプリケーションを起動してください:")
        logger.info("   python src/app.py")
        return False
    
    logger.info("✅ アプリケーションが起動しています")
    
    # 2. 依存関係の確認・インストール
    try:
        import playwright
        logger.info("✅ Playwrightは既にインストールされています")
    except ImportError:
        logger.info("📦 Playwrightをインストール中...")
        if not install_dependencies():
            return False
    
    # 3. E2Eテスト実行
    success = run_e2e_tests()
    
    if success:
        logger.info("🎉 すべてのテストが成功しました")
    else:
        logger.error("💥 テストが失敗しました")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 