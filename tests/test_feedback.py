"""
Structure Feedback Engineのテスト
"""

import pytest
from src.structure_feedback_engine import StructureFeedbackEngine

def test_pytest_collects_this():
    """pytestがテストを検出できることを確認する最小テスト"""
    assert 1 == 1

def test_feedback_engine_initialization():
    """StructureFeedbackEngineの初期化テスト"""
    engine = StructureFeedbackEngine()
    assert isinstance(engine, StructureFeedbackEngine) 