"""
Test Configuration

テストの設定とフィクスチャを提供します。
"""

import pytest
import os
import logging
from typing import Dict, Any
from src.llm.prompts.manager import PromptManager
from src.llm.prompts.prompt_loader import register_all_yaml_templates
from src.common.types import EvaluationResult
from main import create_app
from flask import Flask
from src.llm.controller import AIController
from src.llm.providers import ChatGPTProvider, ClaudeProvider, GeminiProvider
from src.routes import register_routes
from unittest.mock import MagicMock

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def prompt_manager() -> PromptManager:
    """PromptManagerの初期化とテンプレート登録"""
    logger.info("Initializing PromptManager")
    manager = PromptManager()
    register_all_yaml_templates(manager)
    logger.info("Templates registered successfully")
    return manager

@pytest.fixture(scope="session")
def claude_provider(prompt_manager: PromptManager) -> ClaudeProvider:
    """Claudeプロバイダーの初期化"""
    logger.info("Initializing ClaudeProvider")
    return ClaudeProvider(prompt_manager=prompt_manager)

@pytest.fixture(scope="session")
def chatgpt_provider(prompt_manager: PromptManager) -> ChatGPTProvider:
    """ChatGPTプロバイダーの初期化"""
    logger.info("Initializing ChatGPTProvider")
    return ChatGPTProvider(prompt_manager=prompt_manager)

@pytest.fixture(scope="session")
def gemini_provider(prompt_manager: PromptManager) -> GeminiProvider:
    """Geminiプロバイダーの初期化"""
    logger.info("Initializing GeminiProvider")
    return GeminiProvider(prompt_manager=prompt_manager)

@pytest.fixture(scope="session")
def setup_test_environment(prompt_manager: PromptManager, claude_provider: ClaudeProvider, chatgpt_provider: ChatGPTProvider, gemini_provider: GeminiProvider):
    """テスト環境のセットアップ"""
    logger.info("Setting up test environment")
    
    # AIコントローラーの初期化
    ai_controller = AIController(prompt_manager)
    logger.info("AI controller initialized")
    
    return {
        'prompt_manager': prompt_manager,
        'ai_controller': ai_controller,
        'providers': {
            'claude': claude_provider,
            'chatgpt': chatgpt_provider,
            'gemini': gemini_provider
        }
    }

@pytest.fixture
def app():
    """Flaskアプリケーションのフィクスチャ"""
    app = Flask(__name__)
    register_routes(app)
    return app

@pytest.fixture
def client(app):
    """Flaskテストクライアントを返す"""
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_structure_data():
    """サンプルの構造データを提供"""
    return {
        "name": "test_structure",
        "description": "Test structure for evaluation",
        "components": [
            {
                "name": "component1",
                "type": "type1",
                "properties": {"prop1": "value1"}
            },
            {
                "name": "component2",
                "type": "type2",
                "properties": {"prop2": "value2"}
            }
        ]
    }

@pytest.fixture
def test_structure_data():
    """テスト用の構造データを返す"""
    return {
        "title": "テストタイトル",
        "description": "テスト説明",
        "project": "test_project",
        "content": "{\"構成\": {\"セクション1\": \"内容\"}}",
        "is_final": False
    }

@pytest.fixture
def mock_api_key():
    """モックAPIキーを提供するfixture"""
    return "mock_api_key_12345"

@pytest.fixture
def mock_prompt_manager():
    """テスト用のPromptManagerを提供するfixture"""
    manager = PromptManager()
    
    # テスト用のテンプレートを登録
    test_templates = {
        "claude": {
            "test_template": "Hello {name}!",
            "error_template": "Error: {error_message}"
        },
        "chatgpt": {
            "test_template": "Hi {name}!",
            "error_template": "Error: {error_message}"
        },
        "gemini": {
            "test_template": "Hey {name}!",
            "error_template": "Error: {error_message}"
        }
    }
    
    for provider, templates in test_templates.items():
        for name, template in templates.items():
            manager.register_template(provider, name, template)
    
    return manager

@pytest.fixture
def mock_ai_controller(mock_prompt_manager, mock_api_key):
    """テスト用のAIControllerを提供するfixture"""
    controller = AIController(prompt_manager=mock_prompt_manager)
    
    # 各プロバイダーを初期化
    controller.register_provider("claude", ClaudeProvider(mock_prompt_manager, mock_api_key))
    controller.register_provider("chatgpt", ChatGPTProvider(mock_prompt_manager, mock_api_key))
    controller.register_provider("gemini", GeminiProvider(mock_prompt_manager, mock_api_key))
    
    return controller

@pytest.fixture
def app(mock_ai_controller):
    """テスト用のFlaskアプリケーションを提供するfixture"""
    from src.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['AI_CONTROLLER'] = mock_ai_controller
    return app

@pytest.fixture
def client(app):
    """テスト用のFlaskクライアントを提供するfixture"""
    return app.test_client() 