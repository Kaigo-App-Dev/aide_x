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
from src.exceptions import ProviderInitializationError, APIKeyMissingError

def test_claude_provider_initialization(mock_prompt_manager, mock_api_key):
    """ClaudeProviderの初期化テスト"""
    # 正常な初期化
    provider = ClaudeProvider(mock_prompt_manager, mock_api_key)
    assert provider.prompt_manager == mock_prompt_manager
    assert provider.api_key == mock_api_key
    
    # PromptManagerなしでの初期化
    with pytest.raises(ProviderInitializationError) as exc_info:
        ClaudeProvider(None, mock_api_key)
    assert "PromptManager instance is required" in str(exc_info.value)
    
    # APIキーなしでの初期化
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(APIKeyMissingError) as exc_info:
            ClaudeProvider(mock_prompt_manager)
        assert "ANTHROPIC_API_KEY" in str(exc_info.value)

def test_chatgpt_provider_initialization(mock_prompt_manager, mock_api_key):
    """ChatGPTProviderの初期化テスト"""
    # 正常な初期化
    provider = ChatGPTProvider(mock_prompt_manager, mock_api_key)
    assert provider.prompt_manager == mock_prompt_manager
    assert provider.api_key == mock_api_key
    
    # PromptManagerなしでの初期化
    with pytest.raises(ProviderInitializationError) as exc_info:
        ChatGPTProvider(None, mock_api_key)
    assert "PromptManager instance is required" in str(exc_info.value)
    
    # APIキーなしでの初期化
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(APIKeyMissingError) as exc_info:
            ChatGPTProvider(mock_prompt_manager)
        assert "OPENAI_API_KEY" in str(exc_info.value)

def test_gemini_provider_initialization(mock_prompt_manager, mock_api_key):
    """GeminiProviderの初期化テスト"""
    # 正常な初期化
    provider = GeminiProvider(mock_prompt_manager, mock_api_key)
    assert provider.prompt_manager == mock_prompt_manager
    assert provider.api_key == mock_api_key
    
    # PromptManagerなしでの初期化
    with pytest.raises(ProviderInitializationError) as exc_info:
        GeminiProvider(None, mock_api_key)
    assert "PromptManager instance is required" in str(exc_info.value)
    
    # APIキーなしでの初期化
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(APIKeyMissingError) as exc_info:
            GeminiProvider(mock_prompt_manager)
        assert "GEMINI_API_KEY" in str(exc_info.value)

def test_provider_template_access(mock_prompt_manager, mock_api_key):
    """プロバイダーからのテンプレートアクセステスト"""
    # 各プロバイダーを初期化
    claude = ClaudeProvider(mock_prompt_manager, mock_api_key)
    chatgpt = ChatGPTProvider(mock_prompt_manager, mock_api_key)
    gemini = GeminiProvider(mock_prompt_manager, mock_api_key)
    
    # テンプレートの取得をテスト
    assert claude.get_template("test_template") == "Hello {name}!"
    assert chatgpt.get_template("test_template") == "Hi {name}!"
    assert gemini.get_template("test_template") == "Hey {name}!"
    
    # 存在しないテンプレートの取得をテスト
    with pytest.raises(Exception):
        claude.get_template("nonexistent_template") 