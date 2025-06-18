"""
評価機能のテスト

このモジュールは、構造評価機能のテストを提供します。
"""

import pytest
from unittest.mock import patch, MagicMock
from src.structure.evaluator import evaluate_structure
from src.llm.prompts import prompt_manager, PromptManager
from src.common.types import EvaluationResult
from src.exceptions import ProviderError, PromptError

@pytest.fixture
def prompt_manager_fixture():
    """プロンプトマネージャーのフィクスチャ"""
    prompt_manager.register_builtin_templates()
    return prompt_manager

@pytest.fixture
def test_structure():
    """テスト用の構造データ"""
    return {
        "name": "test_structure",
        "type": "test",
        "properties": {
            "prop1": "value1",
            "prop2": "value2"
        }
    }

@pytest.fixture
def mock_successful_response():
    """成功時のレスポンス"""
    return {
        "score": 0.8,
        "is_valid": True,
        "details": {
            "reason": "Valid structure"
        }
    }

@pytest.fixture
def mock_failed_response():
    """失敗時のレスポンス"""
    return {
        "score": 0.3,
        "is_valid": False,
        "details": {
            "reason": "Invalid structure"
        }
    }

def test_evaluate_structure_claude(prompt_manager_fixture):
    """Claudeを使用した構造評価のテスト"""
    structure = """
    タイトル: テスト構造
    説明: これはテスト用の構造です。
    内容:
    - 項目1
    - 項目2
    """
    
    result = evaluate_structure(structure, provider="claude", prompt_manager=prompt_manager_fixture)
    
    assert isinstance(result, EvaluationResult)
    assert isinstance(result.score, float)
    assert 0 <= result.score <= 1
    assert isinstance(result.feedback, str)
    assert isinstance(result.details, dict)
    assert "strengths" in result.details
    assert "weaknesses" in result.details
    assert "suggestions" in result.details
    assert result.is_valid

def test_evaluate_structure_gemini(prompt_manager_fixture):
    """Geminiを使用した構造評価のテスト"""
    structure = """
    タイトル: テスト構造
    説明: これはテスト用の構造です。
    内容:
    - 項目1
    - 項目2
    """
    
    result = evaluate_structure(structure, provider="gemini", prompt_manager=prompt_manager_fixture)
    
    assert isinstance(result, EvaluationResult)
    assert isinstance(result.score, float)
    assert 0 <= result.score <= 1
    assert isinstance(result.feedback, str)
    assert isinstance(result.details, dict)
    assert "strengths" in result.details
    assert "weaknesses" in result.details
    assert "suggestions" in result.details
    assert result.is_valid

def test_evaluate_structure_invalid_provider():
    """無効なプロバイダーでの構造評価のテスト"""
    structure = "テスト構造"
    
    with pytest.raises(ValueError):
        evaluate_structure(structure, provider="invalid_provider")

def test_claude_success(test_structure, mock_successful_response):
    """Claude成功時のテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_evaluate:
        mock_evaluate.return_value = EvaluationResult(
            is_valid=True,
            score=0.8,
            details=mock_successful_response
        )
        
        result = evaluate_structure_with(test_structure, provider_name="claude")
        assert result is not None
        assert result.is_valid
        assert result.score == 0.8
        assert "reason" in result.details

def test_claude_failure_gemini_success(test_structure, mock_failed_response, mock_successful_response):
    """Claude失敗→Gemini成功時のテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_claude:
        mock_claude.return_value = EvaluationResult(
            is_valid=False,
            score=0.3,
            error="Claude evaluation failed",
            details=mock_failed_response
        )
        
        with patch("src.llm.evaluators.gemini_evaluator.GeminiEvaluator.evaluate") as mock_gemini:
            mock_gemini.return_value = EvaluationResult(
                is_valid=True,
                score=0.8,
                details=mock_successful_response
            )
            
            result = evaluate_structure_with(test_structure, provider_name="claude", fallback=True)
            assert result is not None
            assert result.is_valid
            assert result.score == 0.8
            assert "reason" in result.details

def test_both_providers_fail(test_structure, mock_failed_response):
    """両プロバイダー失敗時のテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_claude:
        mock_claude.return_value = EvaluationResult(
            is_valid=False,
            score=0.3,
            error="Claude evaluation failed",
            details=mock_failed_response
        )
        
        with patch("src.llm.evaluators.gemini_evaluator.GeminiEvaluator.evaluate") as mock_gemini:
            mock_gemini.return_value = EvaluationResult(
                is_valid=False,
                score=0.2,
                error="Gemini evaluation failed",
                details=mock_failed_response
            )
            
            result = evaluate_structure_with(test_structure, provider_name="claude", fallback=True)
            assert result is None

def test_invalid_provider_name(test_structure):
    """無効なプロバイダー名のテスト"""
    with pytest.raises(ValueError) as exc_info:
        evaluate_structure_with(test_structure, provider_name="invalid")
    assert "Invalid provider name" in str(exc_info.value)

def test_provider_error_handling(test_structure):
    """プロバイダーエラーのテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_evaluate:
        mock_evaluate.side_effect = ProviderError("claude", "Provider initialization failed")
        
        result = evaluate_structure_with(test_structure, provider_name="claude")
        assert result is None

def test_prompt_error_handling(test_structure):
    """プロンプトエラーのテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_evaluate:
        mock_evaluate.side_effect = PromptError("claude", "structure_evaluation", "Template not found")
        
        result = evaluate_structure_with(test_structure, provider_name="claude")
        assert result is None 