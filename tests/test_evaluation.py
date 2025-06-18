"""
構成評価のテスト

テスト対象の関数:
- evaluate_structure_with: モデルを指定して構成を評価
"""

import pytest
from src.structure.evaluator import evaluate_structure_with
from src.common.types import EvaluationResult
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
    
    assert isinstance(result, EvaluationResult)
    assert result.is_valid
    assert result.score > 0.5
    assert isinstance(result.feedback, str)
    assert isinstance(result.details, dict)
    assert len(result.details) > 0

def test_evaluate_gemini(sample_structure):
    """Geminiを使用した構成評価のテスト"""
    result = evaluate_structure_with("gemini", sample_structure)
    
    assert isinstance(result, EvaluationResult)
    assert result.is_valid
    assert result.score > 0.5
    assert isinstance(result.feedback, str)
    assert isinstance(result.details, dict)
    assert len(result.details) > 0

if __name__ == "__main__":
    pytest.main([__file__])
