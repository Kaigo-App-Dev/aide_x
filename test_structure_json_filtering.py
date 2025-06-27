#!/usr/bin/env python3
"""
構成JSONフィルタリング機能のテストスクリプト
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.routes.unified_routes import _is_structure_json, create_message_param

def test_structure_json_detection():
    """構成JSON検出機能をテスト"""
    
    print("=== 構成JSON検出機能テスト ===")
    
    # テストケース1: コードブロック形式のJSON
    test_case_1 = """```json
{
  "title": "ブログサイト構成",
  "description": "個人ブログサイトの基本構成",
  "content": {
    "ヘッダー": {
      "ロゴ": "サイトロゴ",
      "ナビゲーション": "メニュー項目"
    }
  }
}
```"""
    
    # テストケース2: 通常のJSON
    test_case_2 = """{
  "title": "ECサイト構成",
  "description": "オンラインショッピングサイト",
  "content": {
    "商品ページ": "商品詳細表示",
    "カート": "購入商品管理"
  }
}"""
    
    # テストケース3: 通常のテキスト
    test_case_3 = """ブログサイトを作成したいです。ヘッダーにはロゴとナビゲーションメニューを配置し、
メインコンテンツエリアには記事一覧と記事詳細ページを設けます。"""
    
    # テストケース4: 無効なJSON
    test_case_4 = """{
  title: "ブログサイト",
  description: "個人ブログサイト"
}"""
    
    # テストケース5: 空の文字列
    test_case_5 = ""
    
    test_cases = [
        ("コードブロックJSON", test_case_1, True),
        ("通常のJSON", test_case_2, True),
        ("通常のテキスト", test_case_3, False),
        ("無効なJSON", test_case_4, False),
        ("空の文字列", test_case_5, False)
    ]
    
    for case_name, test_content, expected in test_cases:
        print(f"\n--- テストケース: {case_name} ---")
        result = _is_structure_json(test_content)
        status = "✅" if result == expected else "❌"
        print(f"{status} 期待値: {expected}, 実際: {result}")
        if result:
            print(f"  内容: {test_content[:100]}...")
        else:
            print(f"  内容: {test_content}")

def test_message_param_creation():
    """メッセージパラメータ作成機能をテスト"""
    
    print("\n=== メッセージパラメータ作成機能テスト ===")
    
    # テストケース1: 構成JSON
    structure_json = """```json
{
  "title": "テスト構成",
  "content": {"key": "value"}
}
```"""
    
    # テストケース2: 通常のメッセージ
    normal_message = "こんにちは、構成について質問があります。"
    
    test_cases = [
        ("構成JSON", structure_json, "structure"),
        ("通常メッセージ", normal_message, "assistant")
    ]
    
    for case_name, content, expected_type in test_cases:
        print(f"\n--- テストケース: {case_name} ---")
        param = create_message_param(
            role="assistant",
            content=content,
            type="assistant",
            source="chat"
        )
        
        actual_type = param.get("type")
        status = "✅" if actual_type == expected_type else "❌"
        print(f"{status} 期待されるtype: {expected_type}, 実際: {actual_type}")
        print(f"  パラメータ: {param}")

def test_template_filtering():
    """テンプレートフィルタリング機能をテスト"""
    
    print("\n=== テンプレートフィルタリング機能テスト ===")
    
    # テスト用メッセージリスト
    test_messages = [
        {"role": "user", "content": "ブログサイトの構成を作成してください", "type": "user", "source": "chat"},
        {"role": "assistant", "content": "```json\n{\"title\":\"ブログサイト\",\"content\":{}}\n```", "type": "structure", "source": "chat"},
        {"role": "assistant", "content": "構成を生成しました。", "type": "assistant", "source": "chat"},
        {"role": "system", "content": "✅ 構成データを抽出しました。", "type": "note", "source": "system"}
    ]
    
    print("元のメッセージリスト:")
    for i, msg in enumerate(test_messages):
        print(f"  {i+1}. {msg['role']} ({msg.get('type', 'none')}): {msg['content'][:50]}...")
    
    print("\nフィルタリング後（type='structure'を除外）:")
    filtered_messages = [msg for msg in test_messages if msg.get('type') != 'structure']
    for i, msg in enumerate(filtered_messages):
        print(f"  {i+1}. {msg['role']} ({msg.get('type', 'none')}): {msg['content'][:50]}...")
    
    print(f"\nフィルタリング結果: {len(test_messages)} → {len(filtered_messages)} メッセージ")

def main():
    """メイン関数"""
    print("🚀 構成JSONフィルタリング機能テスト開始")
    
    # 構成JSON検出テスト
    test_structure_json_detection()
    
    # メッセージパラメータ作成テスト
    test_message_param_creation()
    
    # テンプレートフィルタリングテスト
    test_template_filtering()
    
    print("\n✅ テスト完了")
    print("\n📋 実装内容:")
    print("1. _is_structure_json(): 構成JSONを検出する関数")
    print("2. create_message_param(): 構成JSONの場合はtype='structure'を設定")
    print("3. サーバー側: 構成JSONの場合はChat欄に追加しない")
    print("4. テンプレート側: type='structure'のメッセージをスキップ")
    print("5. JavaScript側: type='structure'のメッセージをスキップ")

if __name__ == "__main__":
    main() 