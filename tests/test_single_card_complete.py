#!/usr/bin/env python3
"""
AIDE-X 1モジュール単位（1構成カード）の評価処理テスト

このテストは、AIDE-Xの最小構成が単体で動作することを保証する
「1モジュールの成立確認」に位置づけられます。
"""

import pytest
import sys
import os
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.structure.evaluator import evaluate_structure_with
from src.llm.prompts import prompt_manager
from src.llm.prompts.templates import register_all_templates


def create_simple_structure() -> Dict[str, Any]:
    """
    テスト用の簡単な1カード構成を作成
    
    Returns:
        Dict[str, Any]: テスト用の構成データ
    """
    return {
        "id": "test-structure-001",
        "title": "テストWebアプリ",
        "description": "ユーザー管理機能を持つシンプルなWebアプリケーション",
        "content": {
            "機能": {
                "ユーザー登録": "新規ユーザーの登録機能",
                "ログイン": "既存ユーザーの認証機能",
                "プロフィール管理": "ユーザー情報の編集機能"
            },
            "技術要件": {
                "フロントエンド": "React.js",
                "バックエンド": "Python Flask",
                "データベース": "SQLite"
            }
        },
        "user_requirements": "ユーザー管理機能を持つWebアプリを作成したい",
        "generated_at": "2024-01-01T00:00:00Z",
        "provider": "manual"
    }


def test_single_card_structure_is_evaluated():
    """
    Claudeでの評価を実行し、評価結果が正しい形式であることを検証
    """
    # テンプレートを登録
    register_all_templates(prompt_manager)
    
    # テスト用の簡単な構成を作成
    structure = create_simple_structure()
    
    # Claudeでの評価を実行
    evaluation_result = evaluate_structure_with(structure, "claude", prompt_manager)
    
    # 評価結果が EvaluationResult 型であることを検証
    assert evaluation_result is not None, "評価結果がNoneです"
    
    # is_valid == True であることを検証
    assert evaluation_result.is_valid is True, f"評価結果が無効です: {evaluation_result.feedback}"
    
    # 0.0 <= score <= 1.0 であることを検証
    assert 0.0 <= evaluation_result.score <= 1.0, f"スコアが範囲外です: {evaluation_result.score}"
    
    # feedback に文字列が含まれていることを検証
    assert evaluation_result.feedback is not None, "フィードバックがNoneです"
    assert isinstance(evaluation_result.feedback, str), f"フィードバックが文字列ではありません: {type(evaluation_result.feedback)}"
    assert len(evaluation_result.feedback) > 0, "フィードバックが空です"
    
    # details に辞書が含まれていることを検証
    assert evaluation_result.details is not None, "詳細情報がNoneです"
    assert isinstance(evaluation_result.details, dict), f"詳細情報が辞書ではありません: {type(evaluation_result.details)}"
    
    # 詳細情報に必要なキーが含まれていることを検証（オプション）
    expected_keys = ["intent_match", "clarity", "implementation"]
    for key in expected_keys:
        if key in evaluation_result.details:
            assert evaluation_result.details[key] is not None, f"詳細情報の{key}がNoneです"
    
    print(f"✅ 評価完了:")
    print(f"   - スコア: {evaluation_result.score:.2f}")
    print(f"   - 有効性: {evaluation_result.is_valid}")
    print(f"   - フィードバック: {evaluation_result.feedback[:100]}...")
    print(f"   - 詳細情報キー: {list(evaluation_result.details.keys())}")


def test_evaluation_with_invalid_structure():
    """
    無効な構成での評価テスト
    """
    # テンプレートを登録
    register_all_templates(prompt_manager)
    
    # 無効な構成（空のcontent）
    invalid_structure = {
        "id": "test-invalid-001",
        "title": "無効な構成",
        "description": "",
        "content": {},
        "user_requirements": "",
        "generated_at": "2024-01-01T00:00:00Z",
        "provider": "manual"
    }
    
    # Claudeでの評価を実行
    evaluation_result = evaluate_structure_with(invalid_structure, "claude", prompt_manager)
    
    # 評価結果が存在することを検証
    assert evaluation_result is not None, "評価結果がNoneです"
    
    # 無効な構成の場合、is_valid == False であることを検証
    # または、スコアが低いことを検証
    assert evaluation_result.score < 0.5 or not evaluation_result.is_valid, f"無効な構成なのに高評価です: score={evaluation_result.score}, valid={evaluation_result.is_valid}"


def test_evaluation_provider_availability():
    """
    評価プロバイダーの利用可能性テスト
    """
    # テンプレートを登録
    register_all_templates(prompt_manager)
    
    structure = create_simple_structure()
    
    # 利用可能なプロバイダーをテスト
    providers = ["claude", "gemini"]
    
    for provider in providers:
        try:
            evaluation_result = evaluate_structure_with(structure, provider, prompt_manager)
            assert evaluation_result is not None, f"{provider}の評価結果がNoneです"
            print(f"✅ {provider}での評価成功: score={evaluation_result.score:.2f}")
        except Exception as e:
            print(f"⚠️ {provider}での評価失敗: {str(e)}")
            # プロバイダーが利用できない場合はスキップ
            pytest.skip(f"{provider}プロバイダーが利用できません: {str(e)}")


if __name__ == "__main__":
    # 直接実行時のテスト
    print("🧪 AIDE-X 1モジュール評価テスト開始")
    print("=" * 50)
    
    try:
        test_single_card_structure_is_evaluated()
        print("\n✅ 基本評価テスト成功")
        
        test_evaluation_with_invalid_structure()
        print("✅ 無効構成テスト成功")
        
        test_evaluation_provider_availability()
        print("✅ プロバイダー可用性テスト成功")
        
        print("\n🎉 すべてのテストが成功しました！")
        print("✅ AIDE-Xの1モジュール評価処理が正常に動作しています")
        
    except Exception as e:
        print(f"\n❌ テストが失敗しました: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 