"""
LLM呼び出しのテスト
"""
import pytest
from typing import Dict, Any, List
from src.llm.hub import call_model, LLMHub
from src.llm.providers.claude import ClaudeProvider
from src.llm.providers.base import ChatMessage
from src.llm.prompts.manager import PromptManager
from unittest.mock import patch, MagicMock
from src.llm.prompts.prompt import Prompt

def test_claude_call():
    """Claude APIの呼び出しテスト"""
    prompt_manager = PromptManager()
    prompt_manager.register_template("claude", "test", "Hello, Claude!")
    
    response = call_model(
        provider_name="claude",
        model_name="claude-3-opus-20240229",
        prompt_name="test",
        prompt_manager=prompt_manager
    )
    assert isinstance(response, str)

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
    prompt_manager = PromptManager()
    provider = ClaudeProvider(prompt_manager=prompt_manager, api_key="test_key")
    
    # Promptオブジェクトを作成
    test_prompt = Prompt(
        template="Hello, Claude!",
        description="Test prompt"
    )
    
    response = provider.chat(test_prompt, model_name="claude-3-opus-20240229", prompt_manager=prompt_manager)

    # アサーション
    assert isinstance(response, str)
    assert response == "Hello from Claude!"
    mock_client.messages.create.assert_called_once()

def test_gemini_call():
    """Gemini APIの呼び出しテスト"""
    prompt_manager = PromptManager()
    prompt_manager.register_template("gemini", "test", "Hello, Gemini!")
    
    response = call_model(
        provider_name="gemini",
        model_name="gemini-1.5-flash",
        prompt_name="test",
        prompt_manager=prompt_manager
    )
    assert isinstance(response, str) 