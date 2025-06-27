import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.routes.unified_routes import unified_bp
from src.models.structure import StructureDict


class TestUnifiedInterface:
    """統合インターフェースのテストクラス"""
    
    @pytest.fixture
    def client(self, app):
        """テストクライアント"""
        app.register_blueprint(unified_bp, url_prefix='/unified')
        return app.test_client()
    
    @pytest.fixture
    def empty_structure_data(self):
        """評価履歴が空の構成データ"""
        return {
            "id": "test-structure-empty",
            "title": "テスト構成（空）",
            "description": "評価履歴が空のテスト構成",
            "content": {
                "title": "テストアプリ",
                "description": "テスト用のアプリケーション",
                "content": {
                    "フロントエンド": "React",
                    "バックエンド": "Node.js"
                }
            },
            "evaluations": [],  # 空の評価履歴
            "completions": [],  # 空の補完履歴
            "messages": [],
            "metadata": {}
        }
    
    @pytest.fixture
    def evaluated_structure_data(self):
        """Claude評価済みの構成データ"""
        return {
            "id": "test-structure-evaluated",
            "title": "テスト構成（評価済み）",
            "description": "Claude評価済みのテスト構成",
            "content": {
                "title": "評価済みアプリ",
                "description": "評価済みのアプリケーション",
                "content": {
                    "フロントエンド": "Vue.js",
                    "バックエンド": "Python"
                }
            },
            "evaluations": [
                {
                    "provider": "claude",
                    "score": 0.85,
                    "feedback": "非常に良い構成です。明確で実装可能な設計になっています。",
                    "details": {
                        "strengths": "技術選定が適切で、スケーラビリティを考慮した設計",
                        "weaknesses": "セキュリティ要件の詳細化が必要",
                        "suggestions": [
                            "認証・認可の仕組みを詳細化する",
                            "エラーハンドリングの戦略を追加する",
                            "監視・ログの仕組みを検討する"
                        ],
                        "intent_match": 0.9,
                        "clarity": 0.8
                    },
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "completions": [],  # 空の補完履歴
            "messages": [],
            "metadata": {}
        }
    
    @pytest.fixture
    def improved_structure_data(self):
        """改善構成ありの構成データ"""
        return {
            "id": "test-structure-improved",
            "title": "テスト構成（改善版あり）",
            "description": "改善構成が生成されたテスト構成",
            "content": {
                "title": "改善版アプリ",
                "description": "改善版のアプリケーション",
                "content": {
                    "フロントエンド": "React",
                    "バックエンド": "Node.js"
                }
            },
            "evaluations": [
                {
                    "provider": "claude",
                    "score": 0.75,
                    "feedback": "良い構成ですが、改善の余地があります。",
                    "details": {
                        "strengths": "基本的な設計は良好",
                        "weaknesses": "セキュリティとパフォーマンスの考慮が不足",
                        "suggestions": [
                            "セキュリティ機能を強化する",
                            "パフォーマンス最適化を検討する"
                        ],
                        "intent_match": 0.8,
                        "clarity": 0.7
                    },
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "completions": [],
            "messages": [],
            "metadata": {
                "improved_structure": {
                    "id": "test-structure-improved_improved_20250101_120000",
                    "title": "改善版アプリ（改善版）",
                    "description": "セキュリティとパフォーマンスを強化した改善版",
                    "content": {
                        "title": "改善版アプリ（改善版）",
                        "description": "セキュリティとパフォーマンスを強化したアプリケーション",
                        "content": {
                            "フロントエンド": "React",
                            "バックエンド": "Node.js",
                            "セキュリティ": "JWT認証、HTTPS",
                            "パフォーマンス": "Redis キャッシュ、CDN"
                        }
                    },
                    "metadata": {
                        "original_structure_id": "test-structure-improved",
                        "improvement_timestamp": datetime.now().isoformat(),
                        "claude_suggestions": [
                            "セキュリティ機能を強化する",
                            "パフォーマンス最適化を検討する"
                        ],
                        "provider": "gemini",
                        "type": "improved_structure"
                    }
                }
            }
        }
    
    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_empty_evaluations(self, mock_load_structure, client, empty_structure_data):
        """評価履歴が空の場合のテスト"""
        # モックの設定
        mock_load_structure.return_value = empty_structure_data
        
        # リクエスト実行
        response = client.get('/unified/test-structure-empty')
        
        # ステータスコードの確認（500ではなく200が返る）
        assert response.status_code == 200
        
        # HTMLコンテンツの確認
        html_content = response.data.decode('utf-8')
        
        # 評価カードが空の状態で表示されることを確認
        assert 'まだ評価が実行されていません' in html_content
        assert '評価履歴はありません' in html_content
        
        # エラーメッセージが含まれていないことを確認
        assert 'jinja2.exceptions.UndefinedError' not in html_content
        assert 'UndefinedError' not in html_content
        
        # 基本的なUI要素が表示されることを確認
        assert 'AIDE-X 統合インターフェース' in html_content
        assert '構成ビュー' in html_content
        assert 'チャット' in html_content
    
    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_with_evaluation(self, mock_load_structure, client, evaluated_structure_data):
        """Claude評価済みの場合のテスト"""
        # モックの設定
        mock_load_structure.return_value = evaluated_structure_data
        
        # リクエスト実行
        response = client.get('/unified/test-structure-evaluated')
        
        # ステータスコードの確認
        assert response.status_code == 200
        
        # HTMLコンテンツの確認
        html_content = response.data.decode('utf-8')
        
        # 最新の評価結果が表示されることを確認
        assert '85' in html_content  # スコア85%
        assert '非常に良い構成です' in html_content
        assert '技術選定が適切で、スケーラビリティを考慮した設計' in html_content
        assert 'セキュリティ要件の詳細化が必要' in html_content
        assert '認証・認可の仕組みを詳細化する' in html_content
        assert 'エラーハンドリングの戦略を追加する' in html_content
        assert '監視・ログの仕組みを検討する' in html_content
        
        # 評価詳細が表示されることを確認
        assert '意図一致' in html_content
        assert '明確性' in html_content
        assert '90' in html_content  # intent_match 90%
        assert '80' in html_content  # clarity 80%
        
        # 改善提案が表示されることを確認
        assert '改善提案' in html_content
        assert '強み' in html_content
        assert '改善点' in html_content
    
    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_with_improved_structure(self, mock_load_structure, client, improved_structure_data):
        """改善構成ありの場合のテスト"""
        # モックの設定
        mock_load_structure.return_value = improved_structure_data
        
        # リクエスト実行
        response = client.get('/unified/test-structure-improved')
        
        # ステータスコードの確認
        assert response.status_code == 200
        
        # HTMLコンテンツの確認
        html_content = response.data.decode('utf-8')
        
        # 改善構成カードが表示されることを確認
        assert '改善構成提案' in html_content
        assert 'Gemini生成' in html_content
        assert '改善版アプリ（改善版）' in html_content
        assert 'セキュリティ機能を強化する' in html_content
        assert 'パフォーマンス最適化を検討する' in html_content
        
        # 改善構成のアクションボタンが表示されることを確認
        assert 'Claudeで評価' in html_content
        assert 'この構成を採用' in html_content
        assert '差分表示' in html_content
    
    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_without_improved_structure(self, mock_load_structure, client, evaluated_structure_data):
        """改善構成なしの場合のテスト"""
        # モックの設定（改善構成なし）
        evaluated_structure_data['metadata'] = {}
        mock_load_structure.return_value = evaluated_structure_data
        
        # リクエスト実行
        response = client.get('/unified/test-structure-evaluated')
        
        # ステータスコードの確認
        assert response.status_code == 200
        
        # HTMLコンテンツの確認
        html_content = response.data.decode('utf-8')
        
        # 改善構成カードが表示されないことを確認
        assert '改善構成提案' not in html_content
        assert 'Gemini生成' not in html_content
        
        # 評価結果は正常に表示されることを確認
        assert '85' in html_content  # スコア85%
        assert '非常に良い構成です' in html_content
    
    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_evaluation_html_structure(self, mock_load_structure, client, evaluated_structure_data):
        """評価結果のHTML構造テスト"""
        # モックの設定
        mock_load_structure.return_value = evaluated_structure_data
        
        # リクエスト実行
        response = client.get('/unified/test-structure-evaluated')
        
        # ステータスコードの確認
        assert response.status_code == 200
        
        # HTMLコンテンツの確認
        html_content = response.data.decode('utf-8')
        
        # 評価結果のHTML構造を確認
        assert '<div class="evaluation-card">' in html_content
        assert '<div class="evaluation-header">' in html_content
        assert '<div class="evaluation-score">' in html_content
        assert '<div class="evaluation-feedback">' in html_content
        assert '<div class="evaluation-suggestions">' in html_content
        
        # スコア表示の構造確認
        assert '<div class="score-item">' in html_content
        assert '<div class="score-value">' in html_content
        assert '<div class="score-label">' in html_content
        
        # 改善提案のリスト構造確認
        assert '<ul>' in html_content
        assert '<li>' in html_content
        
        # 強み・弱み・提案の表示確認
        assert '強み:' in html_content
        assert '改善点:' in html_content
        assert '改善提案:' in html_content
    
    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_empty_structure_handling(self, mock_load_structure, client):
        """構成データが空の場合のテスト"""
        # 空の構成データ
        empty_data = {
            "id": "test-structure-completely-empty",
            "title": "",
            "description": "",
            "content": {},
            "evaluations": [],
            "completions": [],
            "messages": [],
            "metadata": {}
        }
        
        # モックの設定
        mock_load_structure.return_value = empty_data
        
        # リクエスト実行
        response = client.get('/unified/test-structure-completely-empty')
        
        # ステータスコードの確認
        assert response.status_code == 200
        
        # HTMLコンテンツの確認
        html_content = response.data.decode('utf-8')
        
        # 空の構成メッセージが表示されることを確認
        assert '構成データがありません' in html_content
        assert 'チャットで構成を作成してみましょう' in html_content
        
        # エラーが発生していないことを確認
        assert 'jinja2.exceptions.UndefinedError' not in html_content
        assert 'UndefinedError' not in html_content
    
    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_malformed_evaluation_data(self, mock_load_structure, client):
        """不正な評価データの場合のテスト"""
        # 不正な評価データ
        malformed_data = {
            "id": "test-structure-malformed",
            "title": "テスト構成",
            "description": "不正な評価データのテスト",
            "content": {
                "title": "テストアプリ",
                "description": "テスト用アプリ"
            },
            "evaluations": [
                {
                    # 不完全な評価データ
                    "provider": "claude",
                    # score や feedback が欠けている
                }
            ],
            "completions": [],
            "messages": [],
            "metadata": {}
        }
        
        # モックの設定
        mock_load_structure.return_value = malformed_data
        
        # リクエスト実行
        response = client.get('/unified/test-structure-malformed')
        
        # ステータスコードの確認（エラーにならない）
        assert response.status_code == 200
        
        # HTMLコンテンツの確認
        html_content = response.data.decode('utf-8')
        
        # エラーが発生していないことを確認
        assert 'jinja2.exceptions.UndefinedError' not in html_content
        assert 'UndefinedError' not in html_content
        
        # 基本的なUIが表示されることを確認
        assert 'AIDE-X 統合インターフェース' in html_content 