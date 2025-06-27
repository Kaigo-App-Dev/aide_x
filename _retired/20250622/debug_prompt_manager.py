#!/usr/bin/env python3
"""
PromptManagerのデバッグスクリプト
"""

import sys
import os
import logging

# ログレベルを設定
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_prompt_manager():
    """PromptManagerの状態をデバッグ"""
    print("=== PromptManager デバッグ ===")
    
    try:
        from src.llm.prompts import prompt_manager
        print(f"✅ prompt_manager インポート成功: {type(prompt_manager)}")
        print(f"prompt_manager.prompts keys: {list(prompt_manager.prompts.keys())}")
        
        # claude.structure_evaluation の存在確認
        claude_key = "claude.structure_evaluation"
        if claude_key in prompt_manager.prompts:
            print(f"✅ {claude_key} が見つかりました")
            prompt = prompt_manager.prompts[claude_key]
            print(f"Prompt: {prompt}")
        else:
            print(f"❌ {claude_key} が見つかりません")
            print(f"利用可能なキー: {[k for k in prompt_manager.prompts.keys() if 'claude' in k]}")
        
        # get_prompt メソッドのテスト
        try:
            prompt = prompt_manager.get_prompt("claude", "structure_evaluation")
            if prompt:
                print(f"✅ get_prompt('claude', 'structure_evaluation') 成功: {prompt}")
            else:
                print("❌ get_prompt('claude', 'structure_evaluation') 失敗: None")
        except Exception as e:
            print(f"❌ get_prompt エラー: {str(e)}")
            
    except Exception as e:
        print(f"❌ prompt_manager インポートエラー: {str(e)}")
        import traceback
        traceback.print_exc()

def test_template_registration():
    """テンプレート登録のテスト"""
    print("\n=== テンプレート登録テスト ===")
    
    try:
        from src.llm.prompts.templates import register_all_templates
        print("✅ register_all_templates インポート成功")
        
        # 登録前の状態確認
        from src.llm.prompts import prompt_manager
        print(f"登録前のprompts数: {len(prompt_manager.prompts)}")
        
        # テンプレート登録（詳細デバッグ）
        print("register_all_templates() 実行開始...")
        register_all_templates()
        print("✅ register_all_templates() 実行完了")
        
        # 登録後の状態確認
        print(f"登録後のprompts数: {len(prompt_manager.prompts)}")
        print(f"登録後のキー: {list(prompt_manager.prompts.keys())}")
        
        # claude.structure_evaluation の確認
        claude_key = "claude.structure_evaluation"
        if claude_key in prompt_manager.prompts:
            print(f"✅ {claude_key} 登録成功")
        else:
            print(f"❌ {claude_key} 登録失敗")
            
    except Exception as e:
        print(f"❌ テンプレート登録エラー: {str(e)}")
        import traceback
        traceback.print_exc()

def test_manual_registration():
    """手動でテンプレート登録をテスト"""
    print("\n=== 手動テンプレート登録テスト ===")
    
    try:
        from src.llm.prompts import prompt_manager
        from src.llm.prompts.manager import Prompt
        
        # 手動でテンプレートを登録
        test_prompt = Prompt(
            name="structure_evaluation",
            provider="claude",
            description="テスト用の構成評価テンプレート",
            template="""以下の構成を評価してください。

{structure}

評価結果は以下のJSON形式で返してください：
{
  \"is_valid\": true,
  \"score\": 0.85,
  \"feedback\": \"構成は概ね妥当です。\",
  \"details\": {}
}
"""
        )
        
        print(f"テストPrompt作成: {test_prompt}")
        prompt_manager.register(test_prompt)
        print("✅ 手動登録完了")
        
        # 確認
        claude_key = "claude.structure_evaluation"
        if claude_key in prompt_manager.prompts:
            print(f"✅ {claude_key} 手動登録成功")
            prompt = prompt_manager.get_prompt("claude", "structure_evaluation")
            print(f"取得したPrompt: {prompt}")
        else:
            print(f"❌ {claude_key} 手動登録失敗")
            
    except Exception as e:
        print(f"❌ 手動登録エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_prompt_manager()
    test_template_registration()
    test_manual_registration() 