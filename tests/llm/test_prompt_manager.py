"""
プロンプトマネージャーのテスト

このモジュールは、プロンプト管理機能のテストを提供します。
"""

import pytest
from src.llm.prompts import prompt_manager, PromptManager
from src.llm.prompts.types import PromptTemplate

def test_prompt_manager_initialization():
    """プロンプトマネージャーの初期化テスト"""
    manager = prompt_manager
    assert isinstance(manager, PromptManager)

def test_register_builtin_templates():
    """組み込みテンプレートの登録テスト"""
    manager = prompt_manager
    manager.register_builtin_templates()
    
    # Claude用のテンプレート確認
    claude_template = manager.get_prompt("evaluation", "claude")
    assert isinstance(claude_template, PromptTemplate)
    assert "structure" in claude_template.template
    assert claude_template.template is not None
    
    # Gemini用のテンプレート確認
    gemini_template = manager.get_prompt("evaluation", "gemini")
    assert isinstance(gemini_template, PromptTemplate)
    assert "structure" in gemini_template.template
    assert gemini_template.template is not None

def test_get_prompt_nonexistent():
    """存在しないプロンプトの取得テスト"""
    manager = prompt_manager
    manager.register_builtin_templates()
    
    # 存在しないプロンプト名
    template = manager.get_prompt("nonexistent", "claude")
    assert template is None
    
    # 存在しないプロバイダー
    template = manager.get_prompt("evaluation", "nonexistent")
    assert template is None

def test_prompt_template_format():
    """プロンプトテンプレートのフォーマットテスト"""
    template = PromptTemplate(
        id="test-id",
        provider="test-provider",
        description="test-desc",
        template="Hello, {placeholder}!"
    )
    formatted = template.format(placeholder="World")
    assert formatted == "Hello, World!" 