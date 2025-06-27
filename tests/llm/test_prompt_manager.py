"""
プロンプトマネージャーのテスト

このモジュールは、プロンプト管理機能のテストを提供します。
"""

import pytest
from src.llm.prompts.manager import PromptManager, PromptAlreadyExistsError
from src.llm.prompts.prompt import Prompt
from src.exceptions import PromptNotFoundError, TemplateFormatError

def test_prompt_manager_initialization(prompt_manager):
    """プロンプトマネージャーの初期化テスト"""
    assert isinstance(prompt_manager, PromptManager)

def test_register_and_get_template(prompt_manager):
    """テンプレートの登録と取得テスト"""
    prompt_manager.register_template("claude", "test", "Hello, {name}!")
    prompt = prompt_manager.get("claude.test")
    assert isinstance(prompt, str)
    assert "{name}" in prompt

def test_register_duplicate_template(prompt_manager):
    """重複テンプレート登録時の例外テスト"""
    prompt_manager.register_template("claude", "dup", "Hi {name}!")
    with pytest.raises(PromptAlreadyExistsError):
        prompt_manager.register_template("claude", "dup", "Hi again {name}!")

def test_get_nonexistent_template(prompt_manager):
    """存在しないテンプレート取得時の例外テスト"""
    with pytest.raises(PromptNotFoundError):
        prompt_manager.get("claude.nonexistent")

def test_prompt_format_success():
    """Promptオブジェクトのformat成功テスト"""
    prompt = Prompt(template="Hello, {placeholder}!")
    formatted = prompt.format(placeholder="World")
    assert formatted == "Hello, World!"

def test_prompt_format_missing_key():
    """Promptオブジェクトのformatでキー不足時の例外テスト"""
    prompt = Prompt(template="Hello, {placeholder}!")
    with pytest.raises(ValueError):
        prompt.format()  # placeholderが無いので例外

def test_register_invalid_template():
    """無効なテンプレート登録時の例外テスト"""
    manager = PromptManager()
    with pytest.raises(TemplateFormatError):
        manager.register_template("claude", "invalid", "Hello {name") 