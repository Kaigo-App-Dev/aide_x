#!/usr/bin/env python3
"""
会話コンテキストの統合テスト実行スクリプト

このスクリプトは会話コンテキストの保存・復元機能を検証するテストを実行します。
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import subprocess
from pathlib import Path

def run_conversation_context_tests():
    """会話コンテキストの統合テストを実行"""
    
    # プロジェクトルートディレクトリを取得
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 会話コンテキストの統合テストを開始します...")
    print(f"📁 作業ディレクトリ: {os.getcwd()}")
    
    # テストファイルのパス
    test_file = "tests/routes/test_conversation_context.py"
    
    if not os.path.exists(test_file):
        print(f"❌ テストファイルが見つかりません: {test_file}")
        return False
    
    # pytestコマンドを構築
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v",  # 詳細出力
        "--tb=short",  # 短いトレースバック
        "--color=yes",  # カラー出力
        "--durations=10",  # 実行時間の表示
        "--maxfail=5"  # 最大5つまで失敗を許容
    ]
    
    print(f"🚀 実行コマンド: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        # テストを実行
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        print("-" * 80)
        
        if result.returncode == 0:
            print("✅ 会話コンテキストの統合テストが成功しました！")
            print("\n📋 テスト結果サマリー:")
            print("  - 会話コンテキストの保存機能 ✅")
            print("  - Claude評価のsource付き保存 ✅")
            print("  - テンプレートでのdata-source表示 ✅")
            print("  - 時系列順での会話表示 ✅")
            print("  - 空メッセージの安全な処理 ✅")
            return True
        else:
            print("❌ 会話コンテキストの統合テストが失敗しました")
            print(f"終了コード: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return False

def main():
    """メイン関数"""
    print("=" * 80)
    print("🎯 AIDE-X 会話コンテキスト統合テスト")
    print("=" * 80)
    
    success = run_conversation_context_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 すべてのテストが成功しました！")
        print("会話コンテキストの保存・復元機能が正常に動作しています。")
    else:
        print("💥 テストが失敗しました。")
        print("会話コンテキストの保存・復元機能に問題がある可能性があります。")
    print("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 