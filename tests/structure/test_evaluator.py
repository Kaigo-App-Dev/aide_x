"""
評価機能のテスト

このモジュールは、構造評価機能のテストを提供します。
"""

import pytest
from unittest.mock import patch, MagicMock
from src.llm.evaluators.claude_evaluator import ClaudeEvaluator
from src.llm.evaluators.gemini_evaluator import GeminiEvaluator
from src.llm.prompts.manager import PromptManager
from src.structure.evaluator import evaluate_structure_with
from src.types import EvaluationResult
from src.exceptions import ProviderError, PromptError

@pytest.fixture
def prompt_manager_fixture():
    """プロンプトマネージャーのフィクスチャ"""
    manager = PromptManager()
    manager.register_template("claude", "structure_evaluation", "以下の構成を評価してください：\n{structure}")
    manager.register_template("gemini", "structure_evaluation", "以下の構成を評価してください：\n{structure}")
    return manager

@pytest.fixture
def test_structure():
    """テスト用の構造データ"""
    return {
        "id": "test-001",
        "title": "テスト構造",
        "description": "テスト用の構造データです",
        "content": {
            "title": "テスト構造",
            "content": {
                "sections": [
                    {"title": "セクション1", "content": "セクション1の内容"},
                    {"title": "セクション2", "content": "セクション2の内容"}
                ]
            }
        },
        "metadata": None,
        "history": None
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

def test_claude_evaluator_success(prompt_manager_fixture, test_structure, mock_successful_response):
    """ClaudeEvaluator成功時のテスト"""
    with patch("src.llm.providers.claude.ClaudeProvider.chat") as mock_chat:
        mock_chat.return_value = mock_successful_response
        evaluator = ClaudeEvaluator()
        result = evaluator.evaluate(test_structure)
        assert result.is_valid
        assert result.score == 0.8
        assert "reason" in dict(result.details)

def test_gemini_evaluator_success(prompt_manager_fixture, test_structure, mock_successful_response):
    """GeminiEvaluator成功時のテスト"""
    with patch("src.llm.providers.gemini.GeminiProvider.chat") as mock_chat:
        mock_chat.return_value = mock_successful_response
        evaluator = GeminiEvaluator()
        result = evaluator.evaluate(test_structure)
        assert result.is_valid
        assert result.score == 0.8
        assert "reason" in dict(result.details)

def test_claude_evaluator_failure(prompt_manager_fixture, test_structure, mock_failed_response):
    """ClaudeEvaluator失敗時のテスト"""
    with patch("src.llm.providers.claude.ClaudeProvider.chat") as mock_chat:
        mock_chat.return_value = mock_failed_response
        evaluator = ClaudeEvaluator()
        result = evaluator.evaluate(test_structure)
        assert result.is_valid
        assert result.score == 0.3
        assert "reason" in dict(result.details)

def test_gemini_evaluator_failure(prompt_manager_fixture, test_structure, mock_failed_response):
    """GeminiEvaluator失敗時のテスト"""
    with patch("src.llm.providers.gemini.GeminiProvider.chat") as mock_chat:
        mock_chat.return_value = mock_failed_response
        evaluator = GeminiEvaluator()
        result = evaluator.evaluate(test_structure)
        assert result.is_valid
        assert result.score == 0.3
        assert "reason" in dict(result.details)

def test_claude_evaluator_provider_error(prompt_manager_fixture, test_structure):
    """ClaudeEvaluatorのプロバイダーエラーテスト"""
    with patch("src.llm.providers.claude.ClaudeProvider.chat") as mock_chat:
        mock_chat.side_effect = ProviderError("claude", "Provider initialization failed")
        evaluator = ClaudeEvaluator()
        with pytest.raises(ProviderError):
            evaluator.evaluate(test_structure)

def test_gemini_evaluator_provider_error(prompt_manager_fixture, test_structure):
    """GeminiEvaluatorのプロバイダーエラーテスト"""
    with patch("src.llm.providers.gemini.GeminiProvider.chat") as mock_chat:
        mock_chat.side_effect = ProviderError("gemini", "Provider initialization failed")
        evaluator = GeminiEvaluator()
        with pytest.raises(ProviderError):
            evaluator.evaluate(test_structure)

def test_claude_evaluator_prompt_error(prompt_manager_fixture, test_structure):
    """ClaudeEvaluatorのプロンプトエラーテスト"""
    with patch("src.llm.providers.claude.ClaudeProvider.chat") as mock_chat:
        mock_chat.side_effect = PromptError("claude", "structure_evaluation", "Template not found")
        evaluator = ClaudeEvaluator()
        with pytest.raises(PromptError):
            evaluator.evaluate(test_structure)

def test_gemini_evaluator_prompt_error(prompt_manager_fixture, test_structure):
    """GeminiEvaluatorのプロンプトエラーテスト"""
    with patch("src.llm.providers.gemini.GeminiProvider.chat") as mock_chat:
        mock_chat.side_effect = PromptError("gemini", "structure_evaluation", "Template not found")
        evaluator = GeminiEvaluator()
        with pytest.raises(PromptError):
            evaluator.evaluate(test_structure)

def test_evaluate_structure_claude(prompt_manager_fixture):
    """Claudeを使用した構造評価のテスト"""
    structure = {
        "id": "test-001",
        "title": "テスト構造",
        "description": "これはテスト用の構造です。",
        "content": {
            "title": "テスト構造",
            "content": {
                "sections": [
                    {"title": "項目1", "content": "項目1の内容"},
                    {"title": "項目2", "content": "項目2の内容"}
                ]
            }
        }
    }
    
    result = evaluate_structure_with(structure, provider="claude")
    
    assert isinstance(result, dict)
    assert isinstance(result.get("score"), float)
    assert 0 <= result.get("score", 0) <= 1
    assert isinstance(result.get("feedback"), str)
    assert isinstance(result.get("details"), dict)
    assert "strengths" in result.get("details", {})
    assert "weaknesses" in result.get("details", {})
    assert "suggestions" in result.get("details", {})
    assert result.get("is_valid")

def test_evaluate_structure_gemini(prompt_manager_fixture):
    """Geminiを使用した構造評価のテスト"""
    structure = {
        "id": "test-002",
        "title": "テスト構造",
        "description": "これはテスト用の構造です。",
        "content": {
            "title": "テスト構造",
            "content": {
                "sections": [
                    {"title": "項目1", "content": "項目1の内容"},
                    {"title": "項目2", "content": "項目2の内容"}
                ]
            }
        }
    }
    
    result = evaluate_structure_with(structure, provider="gemini")
    
    assert isinstance(result, dict)
    assert isinstance(result.get("score"), float)
    assert 0 <= result.get("score", 0) <= 1
    assert isinstance(result.get("feedback"), str)
    assert isinstance(result.get("details"), dict)
    assert "strengths" in result.get("details", {})
    assert "weaknesses" in result.get("details", {})
    assert "suggestions" in result.get("details", {})
    assert result.get("is_valid")

def test_evaluate_structure_invalid_provider():
    """無効なプロバイダーでの構造評価のテスト"""
    structure = {
        "id": "test-003",
        "title": "テスト構造",
        "description": "テスト用の構造です。",
        "content": {
            "title": "テスト構造",
            "content": {
                "sections": [
                    {"title": "項目1", "content": "項目1の内容"}
                ]
            }
        }
    }
    
    with pytest.raises(ValueError):
        evaluate_structure_with(structure, provider="invalid_provider")

def test_claude_success(test_structure, mock_successful_response):
    """Claude成功時のテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_evaluate:
        mock_evaluate.return_value = EvaluationResult(
            score=0.8,
            feedback="Test feedback",
            details=mock_successful_response,
            is_valid=True
        )
        
        result = evaluate_structure_with(test_structure, provider="claude")
        assert result is not None
        assert result["is_valid"]
        assert result["score"] == 0.8
        assert "reason" in dict(result["details"])

def test_claude_failure_gemini_success(test_structure, mock_failed_response, mock_successful_response):
    """Claude失敗→Gemini成功時のテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_claude:
        mock_claude.return_value = EvaluationResult(
            score=0.3,
            feedback="Claude evaluation failed",
            details=mock_failed_response,
            is_valid=False
        )
        
        with patch("src.llm.evaluators.gemini_evaluator.GeminiEvaluator.evaluate") as mock_gemini:
            mock_gemini.return_value = EvaluationResult(
                score=0.8,
                feedback="Test feedback",
                details=mock_successful_response,
                is_valid=True
            )
            
            result = evaluate_structure_with(test_structure, provider="claude")
            assert result is not None
            assert result["is_valid"]
            assert result["score"] == 0.8
            assert "reason" in dict(result["details"])

def test_both_providers_fail(test_structure, mock_failed_response):
    """両プロバイダー失敗時のテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_claude:
        mock_claude.return_value = EvaluationResult(
            score=0.3,
            feedback="Claude evaluation failed",
            details=mock_failed_response,
            is_valid=False
        )
        
        with patch("src.llm.evaluators.gemini_evaluator.GeminiEvaluator.evaluate") as mock_gemini:
            mock_gemini.return_value = EvaluationResult(
                score=0.2,
                feedback="Gemini evaluation failed",
                details=mock_failed_response,
                is_valid=False
            )
            
            result = evaluate_structure_with(test_structure, provider="claude")
            assert result is None

def test_invalid_provider_name(test_structure):
    """無効なプロバイダー名のテスト"""
    with pytest.raises(ValueError) as exc_info:
        evaluate_structure_with(test_structure, provider="invalid")
    assert "Invalid provider name" in str(exc_info.value)

def test_provider_error_handling(test_structure):
    """プロバイダーエラーのテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_evaluate:
        mock_evaluate.side_effect = ProviderError("claude", "Provider initialization failed")
        
        result = evaluate_structure_with(test_structure, provider="claude")
        assert result is None

def test_prompt_error_handling(test_structure):
    """プロンプトエラーのテスト"""
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate") as mock_evaluate:
        mock_evaluate.side_effect = PromptError("claude", "structure_evaluation", "Template not found")
        
        result = evaluate_structure_with(test_structure, provider="claude")
        assert result is None

def test_evaluate_structure():
    """構造評価の基本機能テスト"""
    # テスト用の構造データ
    structure = {
        "id": "test-004",
        "title": "テスト構造",
        "description": "これはテスト用の構造です。",
        "content": {
            "title": "テスト構造",
            "content": {
                "sections": [
                    {"title": "項目1", "content": "項目1の内容"},
                    {"title": "項目2", "content": "項目2の内容"}
                ]
            }
        }
    }
    
    # 評価実行
    result = evaluate_structure_with(structure, provider="claude")
    
    # 結果の検証
    assert isinstance(result, dict)
    assert "score" in result
    assert "feedback" in result
    assert "details" in result
    assert "is_valid" in result
    
    # スコアの範囲チェック
    assert 0 <= result["score"] <= 1.0
    
    # フィードバックの存在確認
    assert isinstance(result["feedback"], str)
    assert len(result["feedback"]) > 0
    
    # 詳細情報の確認
    assert isinstance(result["details"], dict)
    assert "structure_score" in result["details"]
    assert "content_score" in result["details"]
    assert "coherence_score" in result["details"]
    assert "completeness_score" in result["details"]
    
    # 有効性フラグの確認
    assert isinstance(result["is_valid"], bool) 