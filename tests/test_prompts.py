"""
PromptManagerの単体テスト
"""

import pytest
from src.llm.prompts.manager import PromptManager
from src.exceptions import PromptNotFoundError, TemplateFormatError

def test_register_and_get_template(mock_prompt_manager):
    """テンプレートの登録と取得のテスト"""
    # テンプレートの取得をテスト
    template = mock_prompt_manager.get_template("claude", "test_template")
    assert template == "Hello {name}!"
    
    # 別のプロバイダーのテンプレートも取得可能
    template = mock_prompt_manager.get_template("chatgpt", "test_template")
    assert template == "Hi {name}!"
    
    template = mock_prompt_manager.get_template("gemini", "test_template")
    assert template == "Hey {name}!"

def test_get_nonexistent_template(mock_prompt_manager):
    """存在しないテンプレートの取得テスト"""
    with pytest.raises(PromptNotFoundError) as exc_info:
        mock_prompt_manager.get_template("claude", "nonexistent_template")
    
    assert exc_info.value.provider == "claude"
    assert exc_info.value.template_name == "nonexistent_template"
    assert "Template 'nonexistent_template' not found for provider 'claude'" in str(exc_info.value)

def test_format_template(mock_prompt_manager):
    """テンプレートのフォーマットテスト"""
    # 正常なフォーマット
    formatted = mock_prompt_manager.format_template("claude", "test_template", name="Alice")
    assert formatted == "Hello Alice!"
    
    # 別のプロバイダーのテンプレートもフォーマット可能
    formatted = mock_prompt_manager.format_template("chatgpt", "test_template", name="Bob")
    assert formatted == "Hi Bob!"
    
    formatted = mock_prompt_manager.format_template("gemini", "test_template", name="Charlie")
    assert formatted == "Hey Charlie!"

def test_format_template_missing_key(mock_prompt_manager):
    """フォーマットキー不足のテスト"""
    with pytest.raises(TemplateFormatError) as exc_info:
        mock_prompt_manager.format_template("claude", "test_template")
    
    assert exc_info.value.provider == "claude"
    assert exc_info.value.template_name == "test_template"
    assert "Missing required key 'name'" in str(exc_info.value)

def test_register_invalid_template():
    """無効なテンプレートの登録テスト"""
    manager = PromptManager()
    
    # 無効なテンプレート（フォーマット文字列として不正）
    with pytest.raises(TemplateFormatError) as exc_info:
        manager.register_template("test", "invalid", "Hello {name")
    
    assert exc_info.value.provider == "test"
    assert exc_info.value.template_name == "invalid"
    assert "Invalid template format" in str(exc_info.value)

def test_register_duplicate_template(mock_prompt_manager):
    """重複テンプレートの登録テスト"""
    # 同じテンプレートを再登録
    mock_prompt_manager.register_template("claude", "test_template", "Hello {name}!")
    
    # 取得して確認
    template = mock_prompt_manager.get_template("claude", "test_template")
    assert template == "Hello {name}!" 