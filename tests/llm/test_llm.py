"""
LLM呼び出しのテスト
"""
import pytest
from typing import Dict, Any, List
from src.llm.hub import call_model, LLMHub
from src.llm.providers.claude import ClaudeProvider
from src.llm.providers.base import ChatMessage
from unittest.mock import patch, MagicMock

def test_claude_call():
    """Claude APIの呼び出しテスト"""
    prompt = "Hello, Claude!"
    response = call_model(
        model_name="claude-3-opus-20240229",
        prompt=prompt
    )
    assert isinstance(response, dict)
    assert "content" in response
    assert isinstance(response["content"], str)

@patch('anthropic.Anthropic')
def test_claude_provider(mock_anthropic):
    """Claudeプロバイダーのテスト"""
    # モックの設定
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello from Claude!")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    # プロバイダーのインスタンス化とテスト
    provider = ClaudeProvider(api_key="test_key")
    messages = [ChatMessage(role="user", content="Hello, Claude!")]
    response = provider.chat(messages)

    # アサーション
    assert isinstance(response, str)
    assert response == "Hello from Claude!"
    mock_client.messages.create.assert_called_once()

def test_gemini_call():
    """Gemini APIの呼び出しテスト"""
    prompt = "Hello, Gemini!"
    response = call_model(
        model_name="gemini-1.5-flash",
        prompt=prompt
    )
    assert isinstance(response, dict)
    assert "content" in response
    assert isinstance(response["content"], str) 