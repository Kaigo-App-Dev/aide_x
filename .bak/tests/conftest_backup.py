"""
conftest.py: テスト共通のフィクスチャ定義

このファイルは、テスト間で共有される共通のフィクスチャを定義します：
- client: Flaskアプリケーションのテストクライアント
- sample_structure: テスト用のサンプル構成データ
- test_structure_data: テスト用の新規構成データ
"""

import os
import json
import pytest
from datetime import datetime
from typing import TypedDict, List, Optional
import sys
from pathlib import Path
from src.common.exceptions import AIProviderError
from src.llm.prompts import prompt_manager, PromptManager
from main import create_app

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 環境変数の設定
os.environ["OPENAI_API_KEY"] = "dummy-key"
os.environ["ANTHROPIC_API_KEY"] = "dummy-key"
os.environ["GOOGLE_API_KEY"] = "dummy-key"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dummy-credentials.json"

# テスト用APIキーなどの環境変数をセット
os.environ.setdefault("ANTHROPIC_API_KEY", "test_key")
os.environ.setdefault("GEMINI_API_KEY", "test_key")

class EvaluationResult(TypedDict):
    """評価結果の型定義"""
    intent_match: float
    quality_score: float
    intent_reason: str
    improvement_suggestions: List[str]

# PromptManagerのテンプレート登録を必ず実行
try:
    import src.llm.prompts
except ImportError:
    print("Warning: src.llm.prompts module not found. Some tests may fail.")

@pytest.fixture
def client():
    """Flaskアプリケーションのテストクライアントを提供"""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_structure():
    return {
        "title": "テスト構成",
        "sections": [
            {
                "title": "セクション1",
                "content": "テストコンテンツ1"
            },
            {
                "title": "セクション2",
                "content": "テストコンテンツ2"
            }
        ]
    }

@pytest.fixture
def mock_evaluation_result():
    return EvaluationResult(
        intent_match=0.9,
        quality_score=0.85,
        intent_reason="テスト評価理由",
        improvement_suggestions=["テスト改善提案1", "テスト改善提案2"]
    )

@pytest.fixture
def test_structure_data() -> dict:
    """テスト用の新規構成データを提供"""
    return {
        "title": "テストフォーム",
        "description": "自動テスト用",
        "content": json.dumps({
            "title": "テストフォーム",
            "sections": [
                { "name": "名前", "type": "text", "label": "氏名" },
                { "name": "性別", "type": "select", "label": "性別", "options": ["男性", "女性"] }
            ]
        })
    }

@pytest.fixture
def prompt_manager_fixture():
    """PromptManagerのインスタンスを提供するfixture"""
    return prompt_manager

@pytest.fixture
def mock_api_caller():
    """モックAPIコール用のfixture"""
    def _mock_caller(prompt: str) -> dict:
        return {
            "content": '{"is_valid": true, "score": 0.95, "feedback": "構成は概ね良好です", "details": {}}'
        }
    return _mock_caller

@pytest.fixture
def mock_empty_caller():
    """空のレスポンスを返すモックfixture"""
    def _mock_caller(prompt: str) -> dict:
        return {"content": "{}"}
    return _mock_caller

@pytest.fixture
def mock_malformed_caller():
    """不正なJSONを返すモックfixture"""
    def _mock_caller(prompt: str) -> dict:
        return {"content": "invalid json"}
    return _mock_caller

@pytest.fixture
def mock_missing_fields_caller():
    """必須フィールドが欠けているレスポンスを返すモックfixture"""
    def _mock_caller(prompt: str) -> dict:
        return {
            "content": '{"is_valid": true, "score": 0.95}'
        }
    return _mock_caller 