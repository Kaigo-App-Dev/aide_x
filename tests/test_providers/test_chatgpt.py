"""
ChatGPT Provider Tests
"""

import pytest
from unittest.mock import patch, MagicMock
from src.llm.providers.chatgpt import ChatGPTProvider
from src.exceptions import AIProviderError, PromptNotFoundError, APIRequestError, ResponseFormatError
from src.llm.prompts import prompt_manager, PromptManager
from src.llm.providers.base import ChatMessage

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

@pytest.fixture
def mock_openai():
    with patch("openai.OpenAI") as mock:
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_completion
        mock.return_value = mock_client
        yield mock_client

def test_chat_success(mock_prompt_manager, mock_save_log, mock_openai):
    """正常系: チャットが成功し、適切なレスポンスとログが返される"""
    provider = ChatGPTProvider(prompt_manager=mock_prompt_manager)
    messages = [ChatMessage(role="user", content="Test message")]
    
    result = provider.chat(messages, prompt_manager=mock_prompt_manager)
    
    assert result == "Test response"
    mock_save_log.assert_any_call(
        "chatgpt_request",
        {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Test system prompt\nuser: Test message"},
                {"role": "user", "content": "Test message"}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        },
        category="chatgpt"
    )
    mock_save_log.assert_any_call(
        "chatgpt_response",
        {
            "model": "gpt-3.5-turbo",
            "result": "Test response"
        },
        category="chatgpt"
    )

def test_prompt_not_found(mock_prompt_manager, mock_save_log):
    """異常系: プロンプトが見つからない場合"""
    mock_prompt_manager.get_prompt.return_value = None
    
    provider = ChatGPTProvider(prompt_manager=mock_prompt_manager)
    with pytest.raises(PromptNotFoundError) as exc_info:
        provider.chat([ChatMessage(role="user", content="Test message")], prompt_manager=mock_prompt_manager)
    
    assert "Prompt template 'chat' not found for provider 'chatgpt'" in str(exc_info.value)
    mock_save_log.assert_not_called()

def test_api_error(mock_prompt_manager, mock_save_log, mock_openai):
    """異常系: APIリクエストが失敗する場合"""
    mock_openai.chat.completions.create.side_effect = Exception("API error")
    
    provider = ChatGPTProvider(prompt_manager=mock_prompt_manager)
    with pytest.raises(APIRequestError) as exc_info:
        provider.chat([ChatMessage(role="user", content="Test message")], prompt_manager=mock_prompt_manager)
    
    assert "ChatGPT: API request error" in str(exc_info.value)
    mock_save_log.assert_called_once()

def test_empty_response(mock_prompt_manager, mock_save_log, mock_openai):
    """異常系: APIレスポンスが空の場合"""
    mock_openai.chat.completions.create.return_value.choices = []
    
    provider = ChatGPTProvider(prompt_manager=mock_prompt_manager)
    with pytest.raises(ResponseFormatError) as exc_info:
        provider.chat([ChatMessage(role="user", content="Test message")], prompt_manager=mock_prompt_manager)
    
    assert "ChatGPT: Empty response from API" in str(exc_info.value)
    mock_save_log.assert_called_once()

def test_empty_content(mock_prompt_manager, mock_save_log, mock_openai):
    """異常系: APIレスポンスのcontentが空の場合"""
    mock_openai.chat.completions.create.return_value.choices[0].message.content = ""
    
    provider = ChatGPTProvider(prompt_manager=mock_prompt_manager)
    with pytest.raises(ResponseFormatError) as exc_info:
        provider.chat([ChatMessage(role="user", content="Test message")], prompt_manager=mock_prompt_manager)
    
    assert "ChatGPT: Empty content in response" in str(exc_info.value)
    mock_save_log.assert_called_once() 