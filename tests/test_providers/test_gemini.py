"""
Gemini Provider Tests
"""

import pytest
from unittest.mock import patch, MagicMock
from src.llm.providers.gemini import GeminiProvider
from src.common.exceptions import AIProviderError, PromptNotFoundError, APIRequestError, ResponseFormatError
from src.llm.prompts import prompt_manager, PromptManager
from src.llm.providers.base import ChatMessage

@pytest.fixture(autouse=True)
def patch_save_log():
    with patch("src.common.logging_utils.save_log") as mock_save_log:
        yield mock_save_log

@pytest.fixture
def mock_prompt_manager():
    with patch("src.llm.prompts.PromptManager") as mock:
        mock_instance = MagicMock()
        mock_instance.get_prompt.return_value = MagicMock(render=lambda content: f"Test system prompt\n{content}")
        mock.return_value = mock_instance
        yield mock_instance

def test_message_conversion_and_response(mock_prompt_manager, patch_save_log):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key")
        result = provider.chat([
            ChatMessage(role="user", content="Test message")
        ])
        assert result == "Test response"
        patch_save_log.assert_any_call(
            "gemini_request",
            {
                "model": "gemini-pro",
                "prompt": [
                    {"role": "system", "parts": [{"text": "Test system prompt\nuser: Test message"}]},
                    {"role": "user", "parts": [{"text": "Test message"}]}
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            },
            category="gemini"
        )
        patch_save_log.assert_any_call(
            "gemini_response",
            {"model": "gemini-pro", "result": "Test response"},
            category="gemini"
        )

def test_prompt_not_found(mock_prompt_manager, patch_save_log):
    mock_prompt_manager.get_prompt.return_value = None
    provider = GeminiProvider(api_key="dummy-key")
    with pytest.raises(PromptNotFoundError) as exc_info:
        provider.chat([ChatMessage(role="user", content="Test message")])
    assert "Gemini: Prompt not found." in str(exc_info.value)
    patch_save_log.assert_called_once_with(
        "gemini_error",
        {"model": "gemini-pro", "error": "Gemini: Prompt not found."},
        category="gemini"
    )

def test_api_error(mock_prompt_manager, patch_save_log):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API is down")
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key")
        with pytest.raises(APIRequestError) as exc_info:
            provider.chat([ChatMessage(role="user", content="Test message")])
        assert "Gemini: API request error" in str(exc_info.value)
        patch_save_log.assert_any_call(
            "gemini_request",
            {
                "model": "gemini-pro",
                "prompt": [
                    {"role": "system", "parts": [{"text": "Test system prompt\nuser: Test message"}]},
                    {"role": "user", "parts": [{"text": "Test message"}]}
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            },
            category="gemini"
        )

def test_response_format_error(mock_prompt_manager, patch_save_log):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key")
        with pytest.raises(ResponseFormatError) as exc_info:
            provider.chat([ChatMessage(role="user", content="Test message")])
        assert "Gemini: Response format error." in str(exc_info.value)
        patch_save_log.assert_any_call(
            "gemini_request",
            {
                "model": "gemini-pro",
                "prompt": [
                    {"role": "system", "parts": [{"text": "Test system prompt\nuser: Test message"}]},
                    {"role": "user", "parts": [{"text": "Test message"}]}
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            },
            category="gemini"
        )

def test_empty_response(mock_prompt_manager, patch_save_log):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content.return_value = None
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key")
        with pytest.raises(ResponseFormatError):
            provider.chat([ChatMessage(role="user", content="Test message")])

def test_malformed_response(mock_prompt_manager, patch_save_log):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        del mock_response.text
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key")
        with pytest.raises(AIProviderError):
            provider.chat([ChatMessage(role="user", content="Test message")]) 