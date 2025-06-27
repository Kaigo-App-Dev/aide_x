#!/usr/bin/env python3
"""
AIDE-X 複数カード構成の評価テスト
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


def create_multi_card_structure() -> Dict[str, Any]:
    """
    複数カード構成のサンプルを返す
    """
    return {
        "title": "複数機能構成サンプル",
        "content": [
            {
                "title": "ログイン機能",
                "content": {
                    "概要": "ユーザーIDとパスワードによるログイン機能。",
                    "画面": "ログイン画面（ID/Password）",
                    "API": {
                        "endpoint": "/login",
                        "method": "POST"
                    }
                }
            },
            {
                "title": "プロフィール編集",
                "content": {
                    "概要": "ユーザーが自分のプロフィールを編集できる。",
                    "画面": "プロフィール編集画面",
                    "API": {
                        "endpoint": "/profile/update",
                        "method": "PUT"
                    }
                }
            }
        ]
    }


def test_multiple_card_structure_is_evaluated():
    """
    複数カード構成の評価が正しく行われることを検証
    """
    # テンプレートを登録
    register_all_templates(prompt_manager)
    
    structure = create_multi_card_structure()
    
    # Claudeでの評価を実行
    evaluation_result = evaluate_structure_with(structure, "claude", prompt_manager)
    
    # 戻り値がdictまたはEvaluationResultであること
    assert evaluation_result is not None, "評価結果がNoneです"
    assert isinstance(evaluation_result, dict), f"評価結果がdict型ではありません: {type(evaluation_result)}"
    
    # is_validがTrueであること
    assert evaluation_result.get("is_valid") is True, f"is_validがTrueではありません: {evaluation_result}"
    
    # スコアが0.0 < score <= 1.0の範囲
    score = evaluation_result.get("score")
    assert score is not None, "スコアがNoneです"
    assert 0.0 < score <= 1.0, f"スコアが範囲外です: {score}"
    
    # feedbackやdetailsが空でないこと
    feedback = evaluation_result.get("feedback")
    details = evaluation_result.get("details")
    assert feedback and isinstance(feedback, str) and len(feedback) > 0, "feedbackが空です"
    assert details and isinstance(details, dict), "detailsが空またはdict型でありません"
    
    # カードごとの評価結果が含まれていること
    card_results = evaluation_result.get("card_results")
    assert card_results and isinstance(card_results, list) and len(card_results) == 2, "カードごとの評価結果が不正です"
    for card in card_results:
        assert "score" in card and "is_valid" in card and "title" in card, f"カード評価結果の必須フィールドが不足: {card}"
        assert card["is_valid"] is True, f"カードが無効です: {card}"
        assert 0.0 < card["score"] <= 1.0, f"カードスコアが範囲外: {card}"
    
    print(f"✅ 複数カード評価テスト成功: score={score:.2f}, is_valid={evaluation_result.get('is_valid')}")
    print(f"   - フィードバック: {feedback[:100]}...")
    print(f"   - カード数: {len(card_results)}")
    for idx, card in enumerate(card_results):
        print(f"     [{idx}] {card['title']} | score={card['score']:.2f} | valid={card['is_valid']}")


if __name__ == "__main__":
    print("🧪 AIDE-X 複数カード評価テスト開始")
    print("=" * 50)
    test_multiple_card_structure_is_evaluated()
    print("\n🎉 テスト完了") 