#!/usr/bin/env python3
"""
統合インターフェーステスト実行スクリプト

このスクリプトは、unified_interfaceの統合テストを実行し、
テンプレートの安全性とUIの正常動作を確認します。
"""

import sys
import os
import subprocess
import pytest
from pathlib import Path

def run_tests():
    """統合インターフェーステストを実行"""
    
    # プロジェクトルートディレクトリを取得
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 統合インターフェーステストを開始します...")
    print(f"📁 作業ディレクトリ: {os.getcwd()}")
    
    # テストファイルのパス
    test_file = "tests/routes/test_unified_interface.py"
    
    # pytestコマンドの構築
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v",  # 詳細出力
        "--tb=short",  # 短いトレースバック
        "--color=yes",  # カラー出力
        "--durations=10",  # 実行時間の表示
        "--capture=no"  # 出力をキャプチャしない
    ]
    
    try:
        # テスト実行
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ すべてのテストが成功しました！")
            print("\n📊 テスト結果サマリー:")
            print("   - 評価履歴が空の場合の安全性: ✅")
            print("   - Claude評価済みの場合の表示: ✅")
            print("   - 改善構成ありの場合の表示: ✅")
            print("   - 改善構成なしの場合の表示: ✅")
            print("   - HTML構造の検証: ✅")
            print("   - エラーハンドリング: ✅")
            return True
        else:
            print(f"\n❌ テストが失敗しました (終了コード: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n💥 テスト実行中にエラーが発生しました: {e}")
        return False

def run_specific_test(test_name):
    """特定のテストを実行"""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"🧪 特定テストを実行: {test_name}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/routes/test_unified_interface.py::{test_name}",
        "-v",
        "--tb=short",
        "--color=yes",
        "--capture=no"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"💥 テスト実行エラー: {e}")
        return False

def main():
    """メイン関数"""
    
    if len(sys.argv) > 1:
        # 特定のテストを実行
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # すべてのテストを実行
        success = run_tests()
    
    if success:
        print("\n🎉 テスト完了！統合インターフェースは正常に動作しています。")
        sys.exit(0)
    else:
        print("\n💥 テスト失敗！問題を修正してください。")
        sys.exit(1)

if __name__ == "__main__":
    main() 