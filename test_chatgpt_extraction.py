#!/usr/bin/env python3
"""
ChatGPT応答からのJSON抽出テストスクリプト
"""

import json
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.files import extract_json_part, validate_json_string, repair_unquoted_keys
from src.common.logging_utils import setup_logging

def test_chatgpt_extraction():
    """ChatGPT応答からのJSON抽出をテスト"""
    print("🧪 ChatGPT応答からのJSON抽出テスト開始")
    
    # テストケース
    test_cases = [
        {
            "name": "標準的なコードブロック",
            "input": """以下の構成を提案します：

```json
{
  "title": "請求書管理アプリ",
  "description": "請求書の作成・管理・送付を自動化するアプリ",
  "modules": {
    "user_auth": {
      "title": "ユーザー認証",
      "description": "ログイン・ログアウト機能"
    },
    "invoice_creation": {
      "title": "請求書作成",
      "description": "請求書の自動作成機能"
    }
  }
}
```

この構成でいかがでしょうか？""",
            "expected_success": True
        },
        {
            "name": "未クオートキーを含むJSON",
            "input": """構成案：

```json
{
  title: "請求書管理アプリ",
  description: "請求書の作成・管理・送付を自動化するアプリ",
  modules: {
    user_auth: {
      title: "ユーザー認証",
      description: "ログイン・ログアウト機能"
    }
  }
}
```""",
            "expected_success": True
        },
        {
            "name": "日本語キーを含むJSON",
            "input": """以下の構成を提案します：

```json
{
  "タイトル": "請求書管理アプリ",
  "説明": "請求書の作成・管理・送付を自動化するアプリ",
  "モジュール": {
    "認証": {
      "タイトル": "ユーザー認証",
      "説明": "ログイン・ログアウト機能"
    }
  }
}
```""",
            "expected_success": True
        },
        {
            "name": "ChatGPT特有パターン（構成:）",
            "input": """請求書管理アプリの構成を考えてみました。

構成: {
  "title": "請求書管理アプリ",
  "description": "請求書の作成・管理・送付を自動化するアプリ",
  "modules": {
    "user_auth": {
      "title": "ユーザー認証",
      "description": "ログイン・ログアウト機能"
    }
  }
}

この構成でいかがでしょうか？""",
            "expected_success": True
        },
        {
            "name": "プレーンテキスト中のJSON",
            "input": """請求書管理アプリの構成を提案します。

まず、メイン機能として請求書の自動作成機能があります。次に、ユーザー認証機能でセキュリティを確保します。

{
  "title": "請求書管理アプリ",
  "description": "請求書の作成・管理・送付を自動化するアプリ",
  "modules": {
    "user_auth": {
      "title": "ユーザー認証",
      "description": "ログイン・ログアウト機能"
    }
  }
}

この構成でいかがでしょうか？""",
            "expected_success": True
        },
        {
            "name": "不完全なJSON（開き括弧のみ）",
            "input": """構成を提案します：

{
  "title": "請求書管理アプリ",
  "description": "請求書の作成・管理・送付を自動化するアプリ"
  // 閉じ括弧が不足""",
            "expected_success": False
        },
        {
            "name": "空のJSONオブジェクト",
            "input": """構成を提案します：

```json
{}
```

申し訳ありませんが、構成を生成できませんでした。""",
            "expected_success": False
        },
        {
            "name": "JSONを含まないテキスト",
            "input": """請求書管理アプリの構成について考えてみました。

まず、ユーザー認証機能が必要です。ログイン・ログアウト機能を実装します。

次に、請求書作成機能を実装します。ユーザーがデータを入力すると、自動的に請求書が生成されます。

最後に、請求書管理機能を実装します。作成した請求書を一覧表示し、編集・削除が可能です。

この構成でいかがでしょうか？""",
            "expected_success": False
        }
    ]
    
    # テスト実行
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"テストケース {i}/{total_count}: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            # extract_json_part関数を実行
            result = extract_json_part(test_case['input'])
            
            # 結果の判定
            if "error" in result:
                print(f"❌ 抽出失敗: {result['error']}")
                print(f"   理由: {result.get('reason', '不明')}")
                if test_case['expected_success']:
                    print(f"   ⚠️  期待値: 成功、実際: 失敗")
                else:
                    print(f"   ✅ 期待値: 失敗、実際: 失敗（正常）")
                    success_count += 1
            else:
                print(f"✅ 抽出成功")
                print(f"   抽出されたキー: {list(result.keys())}")
                print(f"   抽出された内容: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
                if test_case['expected_success']:
                    print(f"   ✅ 期待値: 成功、実際: 成功")
                    success_count += 1
                else:
                    print(f"   ⚠️  期待値: 失敗、実際: 成功")
            
            # 詳細情報の表示
            if "original_text" in result:
                print(f"   元テキスト: {result['original_text'][:100]}...")
            if "found_keywords" in result and result['found_keywords']:
                print(f"   検出されたキーワード: {result['found_keywords']}")
                
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # 結果の表示
    print(f"\n{'='*60}")
    print(f"テスト結果: {success_count}/{total_count} 成功")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print("🎉 すべてのテストが成功しました！")
        return True
    else:
        print("⚠️  一部のテストが失敗しました")
        return False

def test_specific_structure_extraction(structure_id: str):
    """特定の構成IDのChatGPT応答からのJSON抽出をテスト"""
    print(f"🔍 構成ID {structure_id} のChatGPT応答抽出テスト")
    
    # データファイルのパスを構築
    data_paths = [
        f"data/{structure_id}.json",
        f"structures/{structure_id}.json"
    ]
    
    structure_data = None
    used_path = None
    
    # データファイルを検索
    for path in data_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    structure_data = json.load(f)
                used_path = path
                print(f"✅ データファイル読み込み成功: {path}")
                break
            except Exception as e:
                print(f"❌ データファイル読み込み失敗 {path}: {e}")
    
    if not structure_data:
        print(f"❌ 構成ID {structure_id} のデータファイルが見つかりません")
        return False
    
    # ChatGPT応答を探す
    chatgpt_responses = []
    
    # messagesからChatGPT応答を探す
    if "messages" in structure_data:
        for message in structure_data["messages"]:
            if message.get("source") == "chatgpt" and message.get("role") == "assistant":
                chatgpt_responses.append({
                    "source": "messages",
                    "content": message.get("content", ""),
                    "timestamp": message.get("timestamp", "")
                })
    
    # completionsからChatGPT応答を探す
    if "completions" in structure_data:
        for completion in structure_data["completions"]:
            if completion.get("provider") == "chatgpt":
                chatgpt_responses.append({
                    "source": "completions",
                    "content": completion.get("content", ""),
                    "timestamp": completion.get("timestamp", "")
                })
    
    if not chatgpt_responses:
        print("⚠️  ChatGPT応答が見つかりませんでした")
        return False
    
    print(f"📋 {len(chatgpt_responses)}件のChatGPT応答を発見")
    
    # 各ChatGPT応答をテスト
    for i, response in enumerate(chatgpt_responses, 1):
        print(f"\n{'='*60}")
        print(f"ChatGPT応答 {i}/{len(chatgpt_responses)}")
        print(f"ソース: {response['source']}")
        print(f"タイムスタンプ: {response['timestamp']}")
        print(f"{'='*60}")
        
        try:
            # extract_json_part関数を実行
            result = extract_json_part(response['content'])
            
            # 結果の表示
            if "error" in result:
                print(f"❌ 抽出失敗: {result['error']}")
                print(f"   理由: {result.get('reason', '不明')}")
                if "original_text" in result:
                    print(f"   元テキスト: {result['original_text'][:200]}...")
                if "found_keywords" in result and result['found_keywords']:
                    print(f"   検出されたキーワード: {result['found_keywords']}")
            else:
                print(f"✅ 抽出成功")
                print(f"   抽出されたキー: {list(result.keys())}")
                print(f"   抽出された内容: {json.dumps(result, ensure_ascii=False, indent=2)[:300]}...")
                
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
    
    return True

def main():
    """メイン関数"""
    # ログ設定
    setup_logging()
    
    if len(sys.argv) > 1:
        # 特定の構成IDをテスト
        structure_id = sys.argv[1]
        test_specific_structure_extraction(structure_id)
    else:
        # 標準テストケースを実行
        test_chatgpt_extraction()

if __name__ == "__main__":
    main() 