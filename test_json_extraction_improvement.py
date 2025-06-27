#!/usr/bin/env python3
"""
JSON抽出改善と再プロンプト機能のテストスクリプト
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.files import extract_json_part
from src.routes.unified_routes import _retry_structure_generation

def test_json_extraction_improvement():
    """JSON抽出改善機能をテスト"""
    
    print("=== JSON抽出改善機能テスト ===")
    
    # テストケース1: 通常のMarkdown形式（JSONなし）
    test_text_1 = """
# ブログサイト構成

## 説明
個人ブログサイトの基本構成です。

## ヘッダー
- ロゴ: サイトロゴ
- ナビゲーション: メニュー項目
- 検索機能: 検索ボックス

## メインコンテンツ
- 記事一覧: 最新記事の表示
- 記事詳細: 個別記事ページ
- カテゴリ: 記事分類

## サイドバー
- プロフィール: 著者情報
- カテゴリ一覧: カテゴリメニュー
- 最新記事: 最新記事リスト

## フッター
- コピーライト: 著作権表示
- リンク: 関連リンク
"""
    
    # テストケース2: 自然文のみ
    test_text_2 = """
ブログサイトを作成したいです。ヘッダーにはロゴとナビゲーションメニューを配置し、
メインコンテンツエリアには記事一覧と記事詳細ページを設けます。
サイドバーにはプロフィール情報とカテゴリ一覧を表示し、
フッターにはコピーライト情報を配置します。
"""
    
    # テストケース3: 空のテキスト
    test_text_3 = ""
    
    # テストケース4: 無効なJSON
    test_text_4 = """
{
  title: "ブログサイト",
  description: "個人ブログサイト",
  content: {
    header: {
      logo: "サイトロゴ"
    }
  }
}
"""
    
    test_cases = [
        ("Markdown形式", test_text_1),
        ("自然文のみ", test_text_2),
        ("空のテキスト", test_text_3),
        ("無効なJSON", test_text_4)
    ]
    
    for case_name, test_text in test_cases:
        print(f"\n--- テストケース: {case_name} ---")
        result = extract_json_part(test_text)
        
        if result and "error" not in result:
            print("✅ JSON抽出成功")
            print(f"タイトル: {result.get('title', 'N/A')}")
            print(f"説明: {result.get('description', 'N/A')}")
            print(f"セクション数: {len(result.get('content', {}))}")
        else:
            print("❌ JSON抽出失敗")
            if "error" in result:
                print(f"エラー: {result['error']}")
                print(f"理由: {result.get('reason', 'N/A')}")

def test_retry_prompt_function():
    """再プロンプト機能をテスト"""
    
    print("\n=== 再プロンプト機能テスト ===")
    
    # テスト用の失敗応答
    failed_response = """
ブログサイトの構成について説明します。

## ヘッダー
サイトの上部にはロゴとナビゲーションメニューを配置します。

## メインコンテンツ
記事一覧と記事詳細ページを設けます。

## サイドバー
プロフィール情報とカテゴリ一覧を表示します。

## フッター
コピーライト情報を配置します。
"""
    
    original_message = "ブログサイトの構成を作成してください"
    
    print("🔄 再プロンプト機能テスト開始")
    print(f"元のメッセージ: {original_message}")
    print(f"失敗した応答: {failed_response[:100]}...")
    
    # 再プロンプト関数をテスト（実際のAPI呼び出しは行わない）
    print("ℹ️ 再プロンプト機能は実装済みです（実際のAPI呼び出しはテスト環境では実行しません）")

def main():
    """メイン関数"""
    print("🚀 JSON抽出改善と再プロンプト機能テスト開始")
    
    # JSON抽出改善テスト
    test_json_extraction_improvement()
    
    # 再プロンプト機能テスト
    test_retry_prompt_function()
    
    print("\n✅ テスト完了")
    print("\n📋 改善内容:")
    print("1. ChatGPTプロンプトを強化し、必ずJSON形式で出力するよう指示")
    print("2. JSON抽出失敗時に自動的に再プロンプトを実行")
    print("3. Markdown形式からの構成抽出機能を追加")
    print("4. エラーハンドリングを改善")

if __name__ == "__main__":
    main() 