import pytest
from unittest.mock import patch, MagicMock
from src.llm.hub import call_model
from src.llm.prompts.manager import PromptManager
from src.exceptions import AIProviderError, PromptNotFoundError

@pytest.fixture
def prompt_manager():
    manager = PromptManager()
    # 必要なテンプレートを登録
    manager.register_template("claude", "structure_evaluation", "評価: {structure}")
    manager.register_template("gemini", "structure_evaluation", "評価: {structure}")
    manager.register_template("claude", "chat", "ユーザー: {message}\nアシスタント: ")
    manager.register_template("gemini", "chat", "User: {message}\nAssistant: ")
    return manager

def test_invalid_provider_raises_error(prompt_manager):
    with pytest.raises(AIProviderError):
        call_model("invalid", "model", "structure_evaluation", prompt_manager, structure={"foo": "bar"})

def test_prompt_not_found_raises_error(prompt_manager):
    with pytest.raises(PromptNotFoundError):
        call_model("claude", "model", "not_exist_template", prompt_manager, structure={"foo": "bar"})

def test_provider_chat_method(monkeypatch, prompt_manager):
    # ClaudeProviderのchatをモック
    with patch("src.llm.providers.claude.ClaudeProvider.chat", return_value="mocked response") as mock_chat:
        result = call_model("claude", "model", "structure_evaluation", prompt_manager, structure={"foo": "bar"})
        assert result == "mocked response"
        mock_chat.assert_called_once()

def test_provider_returns_empty(monkeypatch, prompt_manager):
    # GeminiProviderのchatをモックして空文字返す
    with patch("src.llm.providers.gemini.GeminiProvider.chat", return_value="") as mock_chat:
        result = call_model("gemini", "model", "structure_evaluation", prompt_manager, structure={"foo": "bar"})
        assert result == ""
        mock_chat.assert_called_once() 