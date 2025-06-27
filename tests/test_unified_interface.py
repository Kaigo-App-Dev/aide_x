"""
統合インターフェースの評価機能と履歴機能のテスト
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.structure.evaluator import evaluate_structure_with
from src.structure.history_manager import save_structure_history, load_structure_history


class TestUnifiedInterfaceEvaluation:
    """統合インターフェースの評価機能テスト"""
    
    @pytest.fixture
    def sample_structure(self):
        """テスト用の構成データ"""
        return {
            "id": "test_unified_001",
            "title": "テスト統合構成",
            "description": "統合インターフェースのテスト用構成",
            "content": {
                "title": "テストアプリ",
                "description": "テスト用のアプリケーション",
                "content": {
                    "features": ["機能1", "機能2"],
                    "database": "SQLite"
                }
            },
            "metadata": {},
            "messages": []
        }
    
    @pytest.fixture
    def mock_evaluation_result(self):
        """モック評価結果"""
        return {
            "score": 0.85,
            "feedback": "構成は良好です。明確で理解しやすい構造になっています。",
            "details": {
                "intent_match": 0.9,
                "clarity": 0.8,
                "suggestions": [
                    "データベースの詳細設定を追加することを推奨します",
                    "エラーハンドリングの仕組みを検討してください"
                ]
            },
            "is_valid": True
        }
    
    def test_claude_evaluation_integration(self, sample_structure, mock_evaluation_result):
        """Claude評価の統合テスト"""
        with patch('src.structure.evaluator.evaluate_structure_with') as mock_evaluate:
            mock_evaluate.return_value = mock_evaluation_result
            
            # 評価実行
            result = evaluate_structure_with(sample_structure, provider="claude")
            
            # 結果の検証
            assert result["score"] == 0.85
            assert "構成は良好です" in result["feedback"]
            assert result["is_valid"] is True
            assert len(result["details"]["suggestions"]) == 2
            
            # 評価関数が正しく呼ばれたことを確認
            mock_evaluate.assert_called_once_with(sample_structure, provider="claude")
    
    def test_gemini_evaluation_integration(self, sample_structure, mock_evaluation_result):
        """Gemini評価の統合テスト"""
        with patch('src.structure.evaluator.evaluate_structure_with') as mock_evaluate:
            mock_evaluate.return_value = mock_evaluation_result
            
            # 評価実行
            result = evaluate_structure_with(sample_structure, provider="gemini")
            
            # 結果の検証
            assert result["score"] == 0.85
            assert "構成は良好です" in result["feedback"]
            assert result["is_valid"] is True
            
            # 評価関数が正しく呼ばれたことを確認
            mock_evaluate.assert_called_once_with(sample_structure, provider="gemini")
    
    def test_evaluation_with_invalid_structure(self):
        """無効な構成での評価テスト"""
        invalid_structure = {
            "id": "test_invalid",
            "title": "",  # 空のタイトル
            "content": {}  # 空のコンテンツ
        }
        
        result = evaluate_structure_with(invalid_structure, provider="claude")
        
        # 無効な構成は低いスコアになることを確認
        assert result["score"] == 0.0
        assert not result["is_valid"]
        assert "必須フィールド" in result["feedback"] or "不足" in result["feedback"]


class TestUnifiedInterfaceHistory:
    """統合インターフェースの履歴機能テスト"""
    
    @pytest.fixture
    def sample_history_data(self):
        """テスト用の履歴データ"""
        return {
            "structure_id": "test_unified_001",
            "module_id": "test_module",
            "timestamp": datetime.now().isoformat(),
            "history": [
                {
                    "role": "claude",
                    "source": "structure_evaluation",
                    "content": json.dumps({
                        "score": 0.85,
                        "feedback": "Claudeによる評価結果",
                        "details": {"suggestions": ["改善提案1"]},
                        "timestamp": datetime.now().isoformat()
                    }),
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "gemini",
                    "source": "structure_evaluation",
                    "content": json.dumps({
                        "score": 0.78,
                        "feedback": "Geminiによる評価結果",
                        "details": {"suggestions": ["改善提案2"]},
                        "timestamp": datetime.now().isoformat()
                    }),
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
    
    def test_evaluation_history_save_and_load(self, sample_history_data):
        """評価履歴の保存と読み込みテスト"""
        structure_id = "test_unified_001"
        
        # 履歴を保存
        save_result = save_structure_history(
            structure_id=structure_id,
            role="claude",
            source="structure_evaluation",
            content=json.dumps({
                "score": 0.85,
                "feedback": "テスト評価結果",
                "details": {"suggestions": ["テスト提案"]},
                "timestamp": datetime.now().isoformat()
            })
        )
        
        assert save_result is True
        
        # 履歴を読み込み
        loaded_history = load_structure_history(structure_id)
        
        assert loaded_history is not None
        assert loaded_history["structure_id"] == structure_id
        assert len(loaded_history["history"]) >= 1
        
        # 最新の履歴エントリを確認
        latest_entry = loaded_history["history"][-1]
        assert latest_entry["role"] == "claude"
        assert latest_entry["source"] == "structure_evaluation"
        
        # コンテンツの解析
        content_data = json.loads(latest_entry["content"])
        assert content_data["score"] == 0.85
        assert "テスト評価結果" in content_data["feedback"]
    
    def test_multiple_evaluation_history(self, sample_history_data):
        """複数回の評価履歴テスト"""
        structure_id = "test_multiple_001"
        
        # 複数の評価を保存
        evaluations = [
            {"provider": "claude", "score": 0.85, "feedback": "Claude評価1"},
            {"provider": "gemini", "score": 0.78, "feedback": "Gemini評価1"},
            {"provider": "claude", "score": 0.92, "feedback": "Claude評価2"}
        ]
        
        for eval_data in evaluations:
            save_structure_history(
                structure_id=structure_id,
                role=eval_data["provider"],
                source="structure_evaluation",
                content=json.dumps({
                    "score": eval_data["score"],
                    "feedback": eval_data["feedback"],
                    "timestamp": datetime.now().isoformat()
                })
            )
        
        # 履歴を読み込み
        loaded_history = load_structure_history(structure_id)
        
        assert loaded_history is not None
        assert len(loaded_history["history"]) == 3
        
        # 各評価が正しく保存されていることを確認
        roles = [entry["role"] for entry in loaded_history["history"]]
        assert "claude" in roles
        assert "gemini" in roles
        assert roles.count("claude") == 2
        assert roles.count("gemini") == 1


class TestUnifiedInterfaceUI:
    """統合インターフェースUIのテスト"""
    
    def test_evaluation_result_display_format(self):
        """評価結果表示形式のテスト"""
        evaluation_result = {
            "score": 0.85,
            "feedback": "UIテスト用評価結果",
            "details": {
                "intent_match": 0.9,
                "clarity": 0.8,
                "suggestions": [
                    "UI改善提案1",
                    "UI改善提案2"
                ]
            },
            "provider": "claude"
        }
        
        # スコアの表示形式をテスト
        score_display = f"{int(evaluation_result['score'] * 100)}"
        assert score_display == "85"
        
        # フィードバックの存在確認
        assert len(evaluation_result["feedback"]) > 0
        
        # 改善提案の存在確認
        assert len(evaluation_result["details"]["suggestions"]) == 2
        
        # プロバイダー情報の確認
        assert evaluation_result["provider"] in ["claude", "gemini"]
    
    def test_history_item_format(self):
        """履歴アイテム形式のテスト"""
        history_item = {
            "provider": "claude",
            "score": 0.85,
            "feedback": "履歴アイテムテスト",
            "timestamp": datetime.now().isoformat()
        }
        
        # 必須フィールドの確認
        required_fields = ["provider", "score", "feedback", "timestamp"]
        for field in required_fields:
            assert field in history_item
        
        # スコアの範囲確認
        assert 0 <= history_item["score"] <= 1.0
        
        # プロバイダーの妥当性確認
        assert history_item["provider"] in ["claude", "gemini"]
        
        # タイムスタンプの形式確認
        try:
            datetime.fromisoformat(history_item["timestamp"])
        except ValueError:
            pytest.fail("Invalid timestamp format")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 