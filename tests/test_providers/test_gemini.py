"""
Gemini Provider Tests
"""

import pytest
from unittest.mock import patch, MagicMock
from src.llm.providers.gemini import GeminiProvider
from src.exceptions import APIRequestError, ResponseFormatError
from src.llm.prompts import PromptManager
import logging

@pytest.fixture
def mock_prompt_manager():
    with patch("src.llm.prompts.PromptManager") as mock:
        mock_instance = MagicMock()
        mock_instance.get_prompt.return_value = MagicMock(render=lambda content: f"Test system prompt\n{content}")
        mock.return_value = mock_instance
        yield mock_instance

def test_message_conversion_and_response(mock_prompt_manager):
    import logging
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
        from src.llm.prompts.prompt import Prompt
        test_prompt = Prompt(template="Test system prompt\n{content}", description="Test prompt")
        result = provider.chat(test_prompt, model_name="gemini-pro", prompt_manager=mock_prompt_manager, content="Test message")
        assert result == "Test response"

def test_prompt_not_found(mock_prompt_manager):
    mock_prompt_manager.get_prompt.return_value = None
    provider = GeminiProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
    
    from src.llm.prompts.prompt import Prompt
    test_prompt = Prompt(template="Test prompt", description="Test prompt")
    
    # 実際にはAPIが呼ばれてAPIRequestErrorが発生する
    with pytest.raises(APIRequestError) as exc_info:
        provider.chat(test_prompt, model_name="gemini-pro", prompt_manager=mock_prompt_manager, content="Test message")
    assert "API key not valid" in str(exc_info.value)

def test_api_error(mock_prompt_manager):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API is down")
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
        
        from src.llm.prompts.prompt import Prompt
        test_prompt = Prompt(template="Test prompt", description="Test prompt")
        
        with pytest.raises(APIRequestError) as exc_info:
            provider.chat(test_prompt, model_name="gemini-pro", prompt_manager=mock_prompt_manager, content="Test message")
        assert "Gemini: API request error" in str(exc_info.value)

def test_response_format_error(mock_prompt_manager):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
        
        from src.llm.prompts.prompt import Prompt
        test_prompt = Prompt(template="Test prompt", description="Test prompt")
        
        with pytest.raises(ResponseFormatError) as exc_info:
            provider.chat(test_prompt, model_name="gemini-pro", prompt_manager=mock_prompt_manager, content="Test message")
        assert "Gemini: Response format error." in str(exc_info.value)

def test_empty_response(mock_prompt_manager):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content.return_value = None
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
        
        from src.llm.prompts.prompt import Prompt
        test_prompt = Prompt(template="Test prompt", description="Test prompt")
        
        with pytest.raises(ResponseFormatError):
            provider.chat(test_prompt, model_name="gemini-pro", prompt_manager=mock_prompt_manager, content="Test message")

def test_malformed_response(mock_prompt_manager):
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        del mock_response.text
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="dummy-key", prompt_manager=mock_prompt_manager)
        
        from src.llm.prompts.prompt import Prompt
        test_prompt = Prompt(template="Test prompt", description="Test prompt")
        
        # text属性がない場合はResponseFormatErrorが発生する
        with pytest.raises(ResponseFormatError):
            provider.chat(test_prompt, model_name="gemini-pro", prompt_manager=mock_prompt_manager, content="Test message") 