"""
構成評価のテスト

テスト対象の関数:
- evaluate_structure_with: モデルを指定して構成を評価
"""

import pytest
from src.structure.evaluator import evaluate_structure_with
from src.types import EvaluationResult
from src.llm.prompts import prompt_manager, PromptManager
import os
from dotenv import load_dotenv
from typing import Dict, Any
from unittest.mock import patch, MagicMock

load_dotenv()  # カレントディレクトリの .env を読み込み環境変数を設定

@pytest.fixture(autouse=True)
def setup_prompt_manager():
    """プロンプトマネージャーの初期化"""
    # prompt_manager is imported as a singleton

@pytest.fixture
def sample_structure():
    """テスト用のサンプル構造を返す"""
    return {
        "title": "テスト構造",
        "description": "テスト用の構造です",
        "content": {
            "sections": [
                {
                    "title": "セクション1",
                    "content": "セクション1の内容"
                },
                {
                    "title": "セクション2",
                    "content": "セクション2の内容"
                }
            ]
        }
    }

def test_evaluate_claude(sample_structure):
    """Claudeを使用した構成評価のテスト"""
    result = evaluate_structure_with("claude", sample_structure)
    # TypedDictの代わりに辞書のキーと値の型をチェック
    assert isinstance(result, dict)
    assert "is_valid" in result and isinstance(result["is_valid"], bool)
    assert "score" in result and isinstance(result["score"], float)
    assert "feedback" in result and isinstance(result["feedback"], str)
    assert "details" in result and isinstance(result["details"], dict)
    assert result["is_valid"]
    assert result["score"] > 0.5
    assert len(result["details"]) > 0

def test_evaluate_gemini(sample_structure):
    """Geminiを使用した構成評価のテスト"""
    result = evaluate_structure_with("gemini", sample_structure)
    # TypedDictの代わりに辞書のキーと値の型をチェック
    assert isinstance(result, dict)
    assert "is_valid" in result and isinstance(result["is_valid"], bool)
    assert "score" in result and isinstance(result["score"], float)
    assert "feedback" in result and isinstance(result["feedback"], str)
    assert "details" in result and isinstance(result["details"], dict)
    assert result["is_valid"]
    assert result["score"] > 0.5
    assert len(result["details"]) > 0

def test_evaluate_structure_with():
    """構造評価の基本機能テスト"""
    # テスト用の構造データ
    structure = {
        "id": "test-001",
        "title": "テスト構造",
        "description": "テスト用の構造データです",
        "content": {
            "section1": "セクション1の内容",
            "section2": "セクション2の内容"
        }
    }
    # 評価実行
    result = evaluate_structure_with("claude", structure)
    # 結果の検証
    assert isinstance(result, dict)
    assert "is_valid" in result and isinstance(result["is_valid"], bool)
    assert "score" in result and isinstance(result["score"], float)
    assert "feedback" in result and isinstance(result["feedback"], str)
    assert "details" in result and isinstance(result["details"], dict)
    assert 0 <= result["score"] <= 1.0
    assert isinstance(result["feedback"], str)
    assert len(result["feedback"]) > 0
    assert isinstance(result["details"], dict)
    assert "structure_score" in result["details"]
    assert "content_score" in result["details"]

if __name__ == "__main__":
    pytest.main([__file__])
