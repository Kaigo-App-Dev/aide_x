#!/usr/bin/env python3
"""
テンプレート登録状況確認スクリプト
"""

from src.llm.prompts import prompt_manager

def main():
    print("=== プロンプトテンプレート登録状況 ===")
    
    # 登録済みテンプレート一覧
    print("登録済みテンプレート:")
    for key in prompt_manager.prompts.keys():
        print(f"  {key}")
    
    # Claude用structure_evaluationテンプレートの確認
    print("\n=== Claude用structure_evaluationテンプレート ===")
    prompt = prompt_manager.get_prompt('claude', 'structure_evaluation')
    if prompt:
        print("✅ テンプレートが見つかりました")
        print("テンプレート内容（最初の200文字）:")
        print(prompt.template[:200] + "...")
    else:
        print("❌ テンプレートが見つかりません")
    
    # テンプレートのフォーマットテスト
    print("\n=== テンプレートフォーマットテスト ===")
    test_structure = {
        "id": "test-001",
        "title": "テスト構成",
        "description": "テスト用の構成です",
        "content": {"key": "value"}
    }
    
    if prompt:
        try:
            formatted = prompt.template.format(
                structure=str(test_structure)
            )
            print("✅ テンプレートのフォーマットが成功しました")
            print("フォーマット結果（最初の200文字）:")
            print(formatted[:200] + "...")
        except Exception as e:
            print(f"❌ テンプレートのフォーマットに失敗: {e}")
    else:
        print("❌ テンプレートが取得できないため、フォーマットテストをスキップします")

if __name__ == "__main__":
    main() 