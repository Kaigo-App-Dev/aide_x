"""
構成補完誘導メッセージ生成のテスト
"""

import pytest
from src.structure.intervention import generate_intervention_message

class TestGenerateInterventionMessage:
    def test_empty_structure(self):
        state = {"is_empty": True}
        msg = generate_intervention_message(state)
        assert "まだ構成が定義されていません" in msg
        assert "[はい]" in msg

    def test_complete_structure(self):
        state = {
            "is_empty": False,
            "module_count": 2,
            "incomplete_modules": [],
            "missing_fields": []
        }
        msg = generate_intervention_message(state)
        assert msg == ""

    def test_incomplete_structure_single_module(self):
        state = {
            "is_empty": False,
            "module_count": 1,
            "incomplete_modules": [
                {"index": 0, "name": "ユーザー管理", "missing_fields": ["title"]}
            ],
            "missing_fields": ["title", "description"]
        }
        msg = generate_intervention_message(state)
        assert "1個のモジュール" in msg
        assert "title、description" in msg
        assert "[はい]" in msg
        assert "ユーザー管理" in msg
        assert "不足項目を修正" in msg

    def test_incomplete_structure_multi_module(self):
        state = {
            "is_empty": False,
            "module_count": 3,
            "incomplete_modules": [
                {"index": 1, "name": "商品管理", "missing_fields": ["description"]},
                {"index": 2, "name": "注文処理", "missing_fields": ["title"]}
            ],
            "missing_fields": ["title", "description"]
        }
        msg = generate_intervention_message(state)
        assert "3個のモジュール" in msg
        assert "title、description" in msg
        assert "[はい]" in msg
        assert "商品管理" in msg and "注文処理" in msg
        assert "不足項目を修正" in msg

    def test_incomplete_structure_no_missing_fields(self):
        state = {
            "is_empty": False,
            "module_count": 2,
            "incomplete_modules": [
                {"index": 0, "name": "ユーザー管理", "missing_fields": []}
            ],
            "missing_fields": []
        }
        msg = generate_intervention_message(state)
        assert "必須項目" in msg
        assert "ユーザー管理" in msg
        assert "[はい]" in msg 