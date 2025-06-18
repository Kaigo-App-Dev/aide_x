"""
Structure Feedback Engineのテスト
"""

import pytest
import json
from src.structure_feedback_engine import StructureFeedbackEngine
from pathlib import Path

@pytest.fixture
def feedback_engine():
    """StructureFeedbackEngineのフィクスチャ"""
    return StructureFeedbackEngine(log_dir="tests/logs/claude_gemini_diff")

@pytest.fixture
def sample_claude_output():
    """Claudeの出力サンプル"""
    return {
        "title": "テスト構造",
        "description": "テスト用の構造です",
        "content": {
            "section1": {
                "title": "セクション1",
                "items": ["item1", "item2"]
            },
            "section2": {
                "title": "セクション2",
                "items": ["item3", "item4"]
            }
        }
    }

def test_sample():
    assert True

def test_fix_unquoted_keys(feedback_engine):
    """未クオートキーの修正テスト"""
    # テストケース1: 基本的な未クオートキー
    input_json = '{key: "value", nested: {inner: "value"}}'
    expected = '{"key": "value", "nested": {"inner": "value"}}'
    assert json.loads(feedback_engine.fix_unquoted_keys(input_json)) == json.loads(expected)
    
    # テストケース2: 複雑なネスト
    input_json = '''
    {
        outer: {
            middle: {
                inner: "value",
                list: [1, 2, 3]
            }
        }
    }
    '''
    fixed = feedback_engine.fix_unquoted_keys(input_json)
    assert json.loads(fixed) is not None  # パース可能であることを確認

def test_repair_json(feedback_engine, sample_claude_output):
    """JSON修復のテスト"""
    # テストケース1: 未クオートキーを含むJSON
    broken_json = '''
    {
        title: "テスト構造",
        content: {
            section1: {
                title: "セクション1",
                items: ["item1", "item2"]
            }
        }
    }
    '''
    result, was_repaired = feedback_engine.repair_json(broken_json)
    assert was_repaired
    assert result["title"] == "テスト構造"
    
    # テストケース2: 参照JSONを使用した修復
    broken_json = '''
    {
        title: "不完全な構造",
        content: {
            section1: {
                title: "セクション1"
            }
        }
    }
    '''
    result, was_repaired = feedback_engine.repair_json(broken_json, sample_claude_output)
    assert was_repaired
    assert "section2" in result["content"]  # 参照JSONから補完されたことを確認

def test_complement_missing_keys(feedback_engine, sample_claude_output):
    """不足キーの補完テスト"""
    target = {
        "title": "不完全な構造",
        "content": {
            "section1": {
                "title": "セクション1"
            }
        }
    }
    
    result = feedback_engine.complement_missing_keys(target, sample_claude_output)
    assert "description" in result  # トップレベルの不足キーが補完されたことを確認
    assert "items" in result["content"]["section1"]  # ネストされた不足キーが補完されたことを確認
    assert "section2" in result["content"]  # 不足セクションが補完されたことを確認

def test_save_diff_log(feedback_engine, sample_claude_output):
    """差分ログの保存テスト"""
    original = '''
    {
        title: "不完全な構造",
        content: {
            section1: {
                title: "セクション1"
            }
        }
    }
    '''
    repaired = {
        "title": "不完全な構造",
        "description": "テスト用の構造です",
        "content": {
            "section1": {
                "title": "セクション1",
                "items": ["item1", "item2"]
            },
            "section2": {
                "title": "セクション2",
                "items": ["item3", "item4"]
            }
        }
    }
    
    log_file = feedback_engine.save_diff_log(original, repaired, sample_claude_output)
    assert Path(log_file).exists()
    
    # ログファイルの内容を確認
    with open(log_file, "r", encoding="utf-8") as f:
        log_data = json.load(f)
        assert "timestamp" in log_data
        assert "original" in log_data
        assert "repaired" in log_data
        assert "reference" in log_data
        assert "diff" in log_data

def test_process_structure(feedback_engine, sample_claude_output):
    """構造処理の統合テスト"""
    # テストケース1: 未クオートキーを含むJSON
    broken_json = '''
    {
        title: "不完全な構造",
        content: {
            section1: {
                title: "セクション1"
            }
        }
    }
    '''
    result = feedback_engine.process_structure(broken_json, sample_claude_output)
    assert result["title"] == "不完全な構造"
    assert "description" in result
    assert "section2" in result["content"]
    
    # テストケース2: 無効なJSON
    invalid_json = "invalid json"
    with pytest.raises(Exception):
        feedback_engine.process_structure(invalid_json)
    
    # テストケース3: 参照JSONなしでの修復
    result = feedback_engine.process_structure(broken_json)
    assert result["title"] == "不完全な構造"
    assert "content" in result 