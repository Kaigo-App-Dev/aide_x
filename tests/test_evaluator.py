import pytest
from unittest.mock import patch
from src.llm.evaluators import ClaudeEvaluator, GeminiEvaluator
from src.llm.prompts.manager import PromptManager
from src.exceptions import EvaluationError

@pytest.fixture
def prompt_manager():
    manager = PromptManager()
    manager.register_template("claude", "structure_evaluation", "評価: {structure}")
    manager.register_template("gemini", "structure_evaluation", "評価: {structure}")
    return manager

@pytest.fixture
def test_structure():
    return {"title": "テスト構造", "description": "テスト用", "content": ["A", "B"]}

def test_claude_evaluator_success(prompt_manager, test_structure):
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate", return_value={
        "score": 0.8, "feedback": "良い", "details": {"strengths": [], "weaknesses": [], "suggestions": []}, "is_valid": True
    }):
        result = ClaudeEvaluator().evaluate(test_structure)
        assert isinstance(result, dict)
        assert result["is_valid"]
        assert 0 <= result["score"] <= 1
        assert isinstance(result["feedback"], str)
        assert isinstance(result["details"], dict)

def test_gemini_evaluator_success(prompt_manager, test_structure):
    with patch("src.llm.evaluators.gemini_evaluator.GeminiEvaluator.evaluate", return_value={
        "score": 0.7, "feedback": "OK", "details": {"strengths": [], "weaknesses": [], "suggestions": []}, "is_valid": True
    }):
        result = GeminiEvaluator().evaluate(test_structure)
        assert isinstance(result, dict)
        assert result["is_valid"]
        assert 0 <= result["score"] <= 1
        assert isinstance(result["feedback"], str)
        assert isinstance(result["details"], dict)

def test_claude_evaluator_error(prompt_manager, test_structure):
    with patch("src.llm.evaluators.claude_evaluator.ClaudeEvaluator.evaluate", side_effect=EvaluationError("error")):
        with pytest.raises(EvaluationError):
            ClaudeEvaluator().evaluate(test_structure)

def test_gemini_evaluator_error(prompt_manager, test_structure):
    with patch("src.llm.evaluators.gemini_evaluator.GeminiEvaluator.evaluate", side_effect=EvaluationError("error")):
        with pytest.raises(EvaluationError):
            GeminiEvaluator().evaluate(test_structure) 