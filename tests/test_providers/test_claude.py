"""
Claude Provider Tests
"""

import pytest
from unittest.mock import patch, MagicMock
from src.llm.providers.claude import ClaudeProvider
from src.llm.providers.base import ChatMessage
from src.exceptions import PromptNotFoundError, APIRequestError
from src.llm.prompts import prompt_manager, PromptManager

@pytest.fixture
def mock_prompt_manager():
    with patch("src.llm.prompts.PromptManager") as mock:
        mock_instance = MagicMock()
        mock_instance.get_prompt.return_value = MagicMock(render=lambda content: f"Test system prompt\n{content}")
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_save_log():
    with patch("src.logging_utils.save_log") as mock:
        yield mock

def test_message_conversion_and_response(mock_prompt_manager, mock_save_log):
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        provider = ClaudeProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
        
        # Promptオブジェクトを作成
        from src.llm.prompts.prompt import Prompt
        test_prompt = Prompt(template="Test system prompt\n{content}", description="Test prompt")
        
        result = provider.chat(test_prompt, model_name="claude-3-opus-20240229", prompt_manager=mock_prompt_manager)
        assert result == "Test response"
        mock_save_log.assert_any_call(
            "claude_request",
            {
                "model": "claude-3-opus-20240229",
                "messages": [
                    {"role": "system", "content": "Test system prompt\nuser: Test message"},
                    {"role": "user", "content": "Test message"}
                ],
                "max_tokens": 1024,
                "temperature": 0.7
            },
            category="claude"
        )
        mock_save_log.assert_any_call(
            "claude_response",
            {"model": "claude-3-opus-20240229", "result": "Test response"},
            category="claude"
        )

def test_prompt_not_found(mock_prompt_manager, mock_save_log):
    mock_prompt_manager.get_prompt.return_value = None
    provider = ClaudeProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
    
    # Promptオブジェクトを作成
    from src.llm.prompts.prompt import Prompt
    test_prompt = Prompt(template="Test prompt", description="Test prompt")
    
    with pytest.raises(PromptNotFoundError) as exc_info:
        provider.chat(test_prompt, model_name="claude-3-opus-20240229", prompt_manager=mock_prompt_manager)
    assert "Prompt template 'chat' not found for provider 'claude'" in str(exc_info.value)
    mock_save_log.assert_not_called()  # プロンプトが見つからない場合はログ出力なし

def test_api_error(mock_prompt_manager, mock_save_log):
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API is down")
        mock_anthropic.return_value = mock_client

        provider = ClaudeProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
        
        # Promptオブジェクトを作成
        from src.llm.prompts.prompt import Prompt
        test_prompt = Prompt(template="Test prompt", description="Test prompt")
        
        with pytest.raises(APIRequestError) as exc_info:
            provider.chat(test_prompt, model_name="claude-3-opus-20240229", prompt_manager=mock_prompt_manager)
        assert "Claude: API request error" in str(exc_info.value)
        mock_save_log.assert_any_call(
            "claude_request",
            {
                "model": "claude-3-opus-20240229",
                "messages": [
                    {"role": "system", "content": "Test system prompt\nuser: Test message"},
                    {"role": "user", "content": "Test message"}
                ],
                "max_tokens": 1024,
                "temperature": 0.7
            },
            category="claude"
        ) 