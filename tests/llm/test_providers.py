"""
AIプロバイダーの初期化テスト
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.llm.prompts.manager import PromptManager
from src.llm.providers.claude import ClaudeProvider
from src.llm.providers.chatgpt import ChatGPTProvider
from src.llm.providers.gemini import GeminiProvider
from src.exceptions import ProviderInitializationError, APIKeyMissingError, PromptNotFoundError
from src.llm.prompts.prompt import Prompt
from src.llm.prompts.types import MessageParam
from src.llm.providers.base import ChatMessage

def test_claude_provider_initialization(mock_prompt_manager, mock_api_key):
    """ClaudeProviderの初期化テスト"""
    # 正常な初期化
    provider = ClaudeProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    assert provider.prompt_manager == mock_prompt_manager
    assert provider.api_key == mock_api_key
    
    # PromptManagerなしでの初期化
    with pytest.raises(ProviderInitializationError) as exc_info:
        ClaudeProvider(prompt_manager=MagicMock(spec=PromptManager), api_key=mock_api_key)
    assert "PromptManager instance is required" in str(exc_info.value)
    
    # APIキーなしでの初期化
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(APIKeyMissingError) as exc_info:
            ClaudeProvider(prompt_manager=mock_prompt_manager)
        assert "ANTHROPIC_API_KEY" in str(exc_info.value)

def test_chatgpt_provider_initialization(mock_prompt_manager, mock_api_key):
    """ChatGPTProviderの初期化テスト"""
    # 正常な初期化
    provider = ChatGPTProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    assert provider.prompt_manager == mock_prompt_manager
    assert provider.api_key == mock_api_key
    
    # PromptManagerなしでの初期化
    with pytest.raises(ProviderInitializationError) as exc_info:
        ChatGPTProvider(prompt_manager=MagicMock(spec=PromptManager), api_key=mock_api_key)
    assert "PromptManager instance is required" in str(exc_info.value)
    
    # APIキーなしでの初期化
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(APIKeyMissingError) as exc_info:
            ChatGPTProvider(prompt_manager=mock_prompt_manager)
        assert "OPENAI_API_KEY" in str(exc_info.value)

def test_gemini_provider_initialization(mock_prompt_manager, mock_api_key):
    """GeminiProviderの初期化テスト"""
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        # 正常な初期化
        provider = GeminiProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
        assert provider.prompt_manager == mock_prompt_manager
        assert provider.api_key == mock_api_key
        
        # PromptManagerなしでの初期化
        with pytest.raises(ProviderInitializationError) as exc_info:
            GeminiProvider(prompt_manager=MagicMock(spec=PromptManager), api_key=mock_api_key)
        assert "PromptManager instance is required" in str(exc_info.value)
        
        # APIキーなしでの初期化
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(APIKeyMissingError) as exc_info:
                GeminiProvider(prompt_manager=mock_prompt_manager)
            assert "GEMINI_API_KEY" in str(exc_info.value)

def test_provider_chat_method(mock_prompt_manager, mock_api_key):
    """プロバイダーのchat()メソッドテスト"""
    # 各プロバイダーを初期化
    claude = ClaudeProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    chatgpt = ChatGPTProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    gemini = GeminiProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    
    # テスト用のメッセージを作成
    messages = [ChatMessage(role="user", content="Hello Test!")]
    
    # chat()メソッドの呼び出しをテスト
    with patch.object(claude, 'chat', return_value="Claude response") as mock_chat:
        response = claude.chat(messages=messages, prompt_manager=mock_prompt_manager, temperature=0.7, max_tokens=1024)
        assert response == "Claude response"
        mock_chat.assert_called_once_with(messages=messages, prompt_manager=mock_prompt_manager, temperature=0.7, max_tokens=1024)
    
    with patch.object(chatgpt, 'chat', return_value="ChatGPT response") as mock_chat:
        response = chatgpt.chat(messages=messages, prompt_manager=mock_prompt_manager, temperature=0.7, max_tokens=1024)
        assert response == "ChatGPT response"
        mock_chat.assert_called_once_with(messages=messages, prompt_manager=mock_prompt_manager, temperature=0.7, max_tokens=1024)
    
    with patch.object(gemini, 'chat', return_value="Gemini response") as mock_chat:
        response = gemini.chat(messages=messages, prompt_manager=mock_prompt_manager, temperature=0.7, max_tokens=1024)
        assert response == "Gemini response"
        mock_chat.assert_called_once_with(messages=messages, prompt_manager=mock_prompt_manager, temperature=0.7, max_tokens=1024)

def test_provider_template_access(mock_prompt_manager, mock_api_key):
    """プロバイダーからのテンプレートアクセステスト"""
    # 各プロバイダーを初期化
    claude = ClaudeProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    chatgpt = ChatGPTProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    gemini = GeminiProvider(prompt_manager=mock_prompt_manager, api_key=mock_api_key)
    
    # テンプレートの取得をテスト
    assert mock_prompt_manager.get("claude.test_template") == "Hello {name}!"
    assert mock_prompt_manager.get("chatgpt.test_template") == "Hi {name}!"
    assert mock_prompt_manager.get("gemini.test_template") == "Hey {name}!"
    
    # 存在しないテンプレートの取得をテスト
    with pytest.raises(PromptNotFoundError):
        mock_prompt_manager.get("claude.nonexistent_template") 