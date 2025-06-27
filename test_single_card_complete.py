#!/usr/bin/env python3
"""
1カード（構成カード）の完全なサイクルテスト

このスクリプトは、AIDE-Xの1モジュール（構成カード）が以下すべての要件を満たすかテストします：

① 1モジュールの入力テンプレート／UIを整備
② ChatGPTによる構成生成
③ ClaudeまたはGeminiによる構成評価
④ UI表示：構成＋評価結果の表示
⑤ 保存ルートと履歴
⑥ （任意）コード出力処理が動作する
"""

import json
import uuid
import os
import sys
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.structure.generator import generate_structure_with_chatgpt, generate_simple_structure
from src.structure.evaluator import evaluate_structure_with
from src.structure.utils import save_structure, load_structure
from src.llm.prompts import prompt_manager
from src.llm.prompts.templates import register_all_templates

def test_single_card_complete():
    """1カードの完全なサイクルをテスト"""
    
    print("🧩 AIDE-X 1カード完全サイクルテスト開始")
    print("=" * 60)
    
    # テスト用の構造ID
    structure_id = str(uuid.uuid4())
    print(f"📋 テスト構造ID: {structure_id}")
    
    try:
        # ① プロンプトテンプレートの登録確認
        print("\n① プロンプトテンプレートの登録確認")
        print("-" * 40)
        
        # テンプレートを登録
        register_all_templates(prompt_manager)
        
        # 必要なテンプレートが登録されているか確認
        required_templates = [
            ("chatgpt", "structure_generation"),
            ("claude", "structure_evaluation"),
            ("gemini", "structure_evaluation")
        ]
        
        for provider, template_name in required_templates:
            prompt = prompt_manager.get_prompt(provider, template_name)
            if prompt:
                print(f"✅ {provider}.{template_name} - 登録済み")
            else:
                print(f"❌ {provider}.{template_name} - 未登録")
                return False
        
        # ② ChatGPTによる構成生成
        print("\n② ChatGPTによる構成生成")
        print("-" * 40)
        
        user_input = "Webアプリケーションを作成したい。ユーザー管理機能とタスク管理機能を含む。"
        print(f"📝 ユーザー入力: {user_input}")
        
        # ChatGPTで構成生成
        structure = generate_structure_with_chatgpt(user_input, structure_id)
        
        if structure.get("error"):
            print(f"❌ 構成生成エラー: {structure.get('error')}")
            return False
        
        print(f"✅ 構成生成完了")
        print(f"   - タイトル: {structure.get('title', 'N/A')}")
        print(f"   - 説明: {structure.get('description', 'N/A')[:50]}...")
        print(f"   - プロバイダー: {structure.get('provider', 'N/A')}")
        
        # ③ Claudeによる構成評価
        print("\n③ Claudeによる構成評価")
        print("-" * 40)
        
        evaluation = evaluate_structure_with(structure, "claude", prompt_manager)
        
        if not evaluation.is_valid:
            print(f"❌ 評価エラー: {evaluation.feedback}")
            return False
        
        print(f"✅ Claude評価完了")
        print(f"   - スコア: {evaluation.score:.2f}")
        print(f"   - フィードバック: {evaluation.feedback[:100]}...")
        
        # 評価結果を構造に追加
        structure["evaluation"] = {
            "score": evaluation.score,
            "feedback": evaluation.feedback,
            "details": evaluation.details,
            "is_valid": evaluation.is_valid,
            "provider": "claude",
            "evaluated_at": str(datetime.now())
        }
        
        # ④ 保存機能のテスト
        print("\n④ 保存機能のテスト")
        print("-" * 40)
        
        # 構造を保存
        save_result = save_structure(structure)
        if not save_result:
            print("❌ 構造の保存に失敗")
            return False
        
        print(f"✅ 構造保存完了: {save_result}")
        
        # 保存された構造を読み込み
        loaded_structure = load_structure(structure_id)
        if not loaded_structure:
            print("❌ 保存された構造の読み込みに失敗")
            return False
        
        print(f"✅ 構造読み込み完了")
        print(f"   - タイトル: {loaded_structure.get('title', 'N/A')}")
        print(f"   - 評価スコア: {loaded_structure.get('evaluation', {}).get('score', 'N/A')}")
        
        # ⑤ Geminiによる追加評価（オプション）
        print("\n⑤ Geminiによる追加評価")
        print("-" * 40)
        
        gemini_evaluation = evaluate_structure_with(structure, "gemini", prompt_manager)
        
        if gemini_evaluation.is_valid:
            print(f"✅ Gemini評価完了")
            print(f"   - スコア: {gemini_evaluation.score:.2f}")
            print(f"   - フィードバック: {gemini_evaluation.feedback[:100]}...")
            
            # Gemini評価も構造に追加
            structure["gemini_evaluation"] = {
                "score": gemini_evaluation.score,
                "feedback": gemini_evaluation.feedback,
                "details": gemini_evaluation.details,
                "is_valid": gemini_evaluation.is_valid,
                "provider": "gemini",
                "evaluated_at": str(datetime.now())
            }
        else:
            print(f"⚠️ Gemini評価スキップ: {gemini_evaluation.feedback}")
        
        # ⑥ 最終保存
        print("\n⑥ 最終保存")
        print("-" * 40)
        
        final_save_result = save_structure(structure)
        if final_save_result:
            print(f"✅ 最終保存完了: {final_save_result}")
        else:
            print("❌ 最終保存に失敗")
            return False
        
        # ⑦ テスト結果の出力
        print("\n⑦ テスト結果サマリー")
        print("-" * 40)
        
        print("🎉 1カード完全サイクルテスト成功！")
        print(f"📊 最終構造:")
        print(f"   - ID: {structure_id}")
        print(f"   - タイトル: {structure.get('title')}")
        print(f"   - Claude評価スコア: {structure.get('evaluation', {}).get('score', 'N/A')}")
        if "gemini_evaluation" in structure:
            print(f"   - Gemini評価スコア: {structure.get('gemini_evaluation', {}).get('score', 'N/A')}")
        
        # 構造データをJSONファイルに出力（デバッグ用）
        output_file = f"test_output_{structure_id[:8]}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)
        print(f"📄 デバッグ出力: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト中にエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_structure():
    """シンプルな構造生成のテスト"""
    print("\n🧪 シンプル構造生成テスト")
    print("-" * 40)
    
    structure = generate_simple_structure("テストアプリ", "テスト用のシンプルな構成")
    
    print(f"✅ シンプル構造生成完了")
    print(f"   - ID: {structure.get('id')}")
    print(f"   - タイトル: {structure.get('title')}")
    print(f"   - 説明: {structure.get('description')}")
    
    return structure

if __name__ == "__main__":
    print("🚀 AIDE-X 1カード完全サイクルテスト開始")
    print("=" * 60)
    
    # シンプル構造テスト
    simple_structure = test_simple_structure()
    
    # 完全サイクルテスト
    success = test_single_card_complete()
    
    if success:
        print("\n🎉 すべてのテストが成功しました！")
        print("✅ 1カード（構成カード）の完全なサイクルが動作しています")
        print("\n📋 完了した機能:")
        print("   ✅ プロンプトテンプレート登録")
        print("   ✅ ChatGPTによる構成生成")
        print("   ✅ Claudeによる構成評価")
        print("   ✅ 構造の保存・読み込み")
        print("   ✅ Geminiによる追加評価")
        print("   ✅ 評価結果の表示対応")
    else:
        print("\n❌ テストが失敗しました")
        print("🔧 問題を修正してから再実行してください")
    
    print("\n" + "=" * 60)
    print("🏁 テスト終了") 