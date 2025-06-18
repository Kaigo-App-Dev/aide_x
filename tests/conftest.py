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
from src.types import EvaluationResult
from main import create_app
from flask import Flask
from src.llm.controller import AIController
from src.llm.providers import ChatGPTProvider, ClaudeProvider, GeminiProvider
from src.routes import register_routes
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_templates() -> Dict[str, Dict[str, str]]:
    """テスト用のテンプレートを読み込む"""
    templates = {
        "claude": {
            "structure_evaluation": """
            以下の構造を評価してください：
            {structure}
            
            評価基準：
            1. 構造の一貫性
            2. 内容の完全性
            3. 命名規則の適切性
            
            評価結果は以下の形式で返してください：
            {
                "score": 0.8,
                "is_valid": true,
                "details": {
                    "strengths": ["強み1", "強み2"],
                    "weaknesses": ["弱み1", "弱み2"],
                    "suggestions": ["提案1", "提案2"]
                }
            }
            """,
            "chat": "ユーザー: {message}\nアシスタント: "
        },
        "chatgpt": {
            "structure_evaluation": """
            Evaluate the following structure:
            {structure}
            
            Evaluation criteria:
            1. Structure consistency
            2. Content completeness
            3. Naming convention appropriateness
            
            Return the evaluation result in the following format:
            {
                "score": 0.8,
                "is_valid": true,
                "details": {
                    "strengths": ["strength1", "strength2"],
                    "weaknesses": ["weakness1", "weakness2"],
                    "suggestions": ["suggestion1", "suggestion2"]
                }
            }
            """,
            "chat": "User: {message}\nAssistant: "
        },
        "gemini": {
            "structure_evaluation": """
            Evaluate the following structure:
            {structure}
            
            Evaluation criteria:
            1. Structure consistency
            2. Content completeness
            3. Naming convention appropriateness
            
            Return the evaluation result in the following format:
            {
                "score": 0.8,
                "is_valid": true,
                "details": {
                    "strengths": ["strength1", "strength2"],
                    "weaknesses": ["weakness1", "weakness2"],
                    "suggestions": ["suggestion1", "suggestion2"]
                }
            }
            """,
            "chat": "User: {message}\nAssistant: "
        }
    }
    return templates

@pytest.fixture(scope="session")
def prompt_manager() -> PromptManager:
    """PromptManagerの初期化とテンプレート登録"""
    logger.info("Initializing PromptManager")
    manager = PromptManager()
    
    # テスト用のテンプレートを登録
    test_templates = load_test_templates()
    for provider, templates in test_templates.items():
        for name, template in templates.items():
            manager.register_template(provider, name, template)
    
    # YAMLテンプレートも登録
    register_all_yaml_templates(manager)
    
    logger.info("Templates registered successfully")
    return manager

@pytest.fixture(scope="session")
def claude_provider(prompt_manager: PromptManager) -> ClaudeProvider:
    """Claudeプロバイダーの初期化"""
    logger.info("Initializing ClaudeProvider")
    with patch("src.llm.providers.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [{"text": "Test response"}]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.Anthropic.return_value = mock_client
        return ClaudeProvider(prompt_manager=prompt_manager)

@pytest.fixture(scope="session")
def chatgpt_provider(prompt_manager: PromptManager) -> ChatGPTProvider:
    """ChatGPTプロバイダーの初期化"""
    logger.info("Initializing ChatGPTProvider")
    with patch("src.llm.providers.chatgpt.openai") as mock_openai:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client
        return ChatGPTProvider(prompt_manager=prompt_manager)

@pytest.fixture(scope="session")
def gemini_provider(prompt_manager: PromptManager) -> GeminiProvider:
    """Geminiプロバイダーの初期化"""
    logger.info("Initializing GeminiProvider")
    with patch("src.llm.providers.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        provider = GeminiProvider(prompt_manager=prompt_manager)
        return provider

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

# テスト用の環境変数を設定
os.environ.setdefault("GOOGLE_API_KEY", "dummy_key")
os.environ.setdefault("CLAUDE_API_KEY", "dummy_key")
os.environ.setdefault("OPENAI_API_KEY", "dummy_key")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("FLASK_DEBUG", "True")
os.environ.setdefault("LOG_LEVEL", "DEBUG") 