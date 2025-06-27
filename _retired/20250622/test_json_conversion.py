#!/usr/bin/env python3
"""
ChatGPT応答のJSON変換処理テストスクリプト
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# テンプレート登録
from src.llm.prompts.templates import register_all_templates
from src.llm.prompts import prompt_manager
register_all_templates(prompt_manager)

def test_json_string_conversion():
    """JSON文字列からdictへの変換テスト"""
    print("=== JSON文字列変換テスト ===")
    
    # テスト用のstructure（contentがJSON文字列）
    test_structure = {
        "id": "test-001",
        "title": "テスト構成",
        "description": "テスト用の構成です",
        "content": json.dumps({
            "pages": {
                "ログインページ": {
                    "fields": ["ユーザーID", "パスワード"],
                    "validation": ["必須入力"]
                }
            }
        }, ensure_ascii=False, indent=2)
    }
    
    print(f"変換前のcontent型: {type(test_structure['content'])}")
    print(f"変換前のcontent: {test_structure['content'][:100]}...")
    
    # JSON変換処理をシミュレート
    structure_content = test_structure.get("content")
    if isinstance(structure_content, str):
        try:
            structure_content = json.loads(structure_content)
            test_structure["content"] = structure_content
            print(f"✅ JSON変換成功: {type(structure_content)}")
            print(f"変換後のcontent keys: {list(structure_content.keys())}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON変換失敗: {str(e)}")
    
    return test_structure

def test_invalid_json_handling():
    """無効なJSONの処理テスト"""
    print("\n=== 無効なJSON処理テスト ===")
    
    # 無効なJSON文字列
    invalid_json_structure = {
        "id": "test-002",
        "title": "テスト構成2",
        "description": "無効なJSONのテスト",
        "content": "これは有効なJSONではありません"
    }
    
    print(f"無効なcontent: {invalid_json_structure['content']}")
    
    # JSON変換処理をシミュレート
    structure_content = invalid_json_structure.get("content")
    if isinstance(structure_content, str):
        try:
            structure_content = json.loads(structure_content)
            invalid_json_structure["content"] = structure_content
            print(f"✅ JSON変換成功: {type(structure_content)}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON変換失敗（期待通り）: {str(e)}")
            print("⚠️ この場合はClaude評価をスキップすべき")
    
    return invalid_json_structure

def test_evaluate_structure_with():
    """evaluate_structure_withのテスト"""
    print("\n=== evaluate_structure_with テスト ===")
    
    try:
        from src.structure.evaluator import evaluate_structure_with
        from src.llm.prompts import prompt_manager
        
        # テンプレート登録状況を確認
        print(f"prompt_manager.prompts keys: {list(prompt_manager.prompts.keys())}")
        claude_key = "claude.structure_evaluation"
        if claude_key in prompt_manager.prompts:
            print(f"✅ {claude_key} が見つかりました")
        else:
            print(f"❌ {claude_key} が見つかりません")
            return
        
        # 正常なdict型のcontent
        valid_structure = {
            "id": "test-003",
            "title": "テスト構成3",
            "description": "正常なdict型のテスト",
            "content": {
                "pages": {
                    "テストページ": {
                        "fields": ["フィールド1", "フィールド2"],
                        "validation": ["必須チェック"]
                    }
                }
            }
        }
        
        print(f"テスト構造のcontent型: {type(valid_structure['content'])}")
        print(f"content keys: {list(valid_structure['content'].keys())}")
        
        # Claude評価を実行
        result = evaluate_structure_with("claude", valid_structure, prompt_manager)
        print(f"✅ 評価完了: {result}")
        print(f"スコア: {result.score}")
        print(f"フィードバック: {result.feedback}")
        print(f"詳細: {result.details}")
        print(f"有効: {result.is_valid}")
        
    except Exception as e:
        print(f"❌ 評価エラー: {str(e)}")
        import traceback
        traceback.print_exc()

def test_extract_json_part():
    """extract_json_partのテスト"""
    print("\n=== extract_json_part テスト ===")
    
    try:
        from src.utils.files import extract_json_part
        
        # ChatGPT応答のサンプル（JSONを含む）
        chatgpt_response = """
        以下の構成テンプレートを提案します：

        {
            "title": "ユーザー管理システム",
            "description": "ユーザーの登録・認証・管理を行うシステム",
            "content": {
                "pages": {
                    "ログインページ": {
                        "fields": ["ユーザーID", "パスワード", "ログインボタン"],
                        "validation": ["必須入力", "パスワード強度チェック"]
                    }
                }
            }
        }
        """
        
        extracted = extract_json_part(chatgpt_response)
        if extracted:
            print("✅ JSON抽出成功")
            print(f"抽出されたキー: {list(extracted.keys())}")
            if "content" in extracted:
                print(f"content キー: {list(extracted['content'].keys())}")
        else:
            print("❌ JSON抽出失敗")
            
    except Exception as e:
        print(f"❌ extract_json_part エラー: {str(e)}")

def main():
    """メイン関数"""
    print("🧪 ChatGPT応答のJSON変換処理テスト")
    print("=" * 50)
    
    # JSON文字列変換テスト
    test_json_string_conversion()
    
    # 無効なJSON処理テスト
    test_invalid_json_handling()
    
    # extract_json_partテスト
    test_extract_json_part()
    
    # evaluate_structure_withテスト
    test_evaluate_structure_with()

if __name__ == "__main__":
    main() 