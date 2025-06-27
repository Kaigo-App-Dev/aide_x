import json
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import cast
from src.structure.utils import load_structure_by_id, save_structure, StructureDict
from src.llm.evaluators import EvaluationResult
from src.app import create_app

@pytest.fixture
def mock_load_structure():
    """load_structure_by_idのモック"""
    with patch('src.routes.unified_routes.load_structure_by_id') as mock:
        yield mock

@pytest.fixture
def mock_load_evaluation_completion_history():
    """load_evaluation_completion_historyのモック"""
    with patch('src.routes.unified_routes.load_evaluation_completion_history') as mock:
        yield mock

@pytest.fixture
def mock_save_structure():
    """save_structureのモック"""
    with patch('src.routes.unified_routes.save_structure') as mock:
        yield mock

@pytest.fixture
def app():
    """テスト用アプリケーションを作成"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # CSRF保護を無効化
    
    # 一時ディレクトリをデータディレクトリとして設定
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['AIDEX_DATA_DIR'] = temp_dir
        yield app

@pytest.fixture
def client(app):
    """テストクライアントを作成"""
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_structure():
    """テスト用のサンプル構造データ"""
    return {
        "id": "test_structure_001",
        "title": "テスト構造",
        "description": "テスト用の構造データ",
        "content": {
            "title": "テストプロジェクト",
            "description": "テスト用のプロジェクト説明",
            "content": {
                "module1": "テストモジュール1",
                "module2": "テストモジュール2"
            }
        },
        "evaluations": [
            {
                "provider": "claude",
                "score": 0.85,
                "feedback": "良い構造です。改善の余地があります。",
                "details": {
                    "intent_match": 0.9,
                    "clarity": 0.8,
                    "suggestions": ["モジュール名をより具体的にしてください"]
                },
                "timestamp": "2025-06-22T10:30:00",
                "structure_id": "test_structure_001"
            }
        ],
        "completions": [
            {
                "provider": "gemini",
                "content": "改善された構造:\n- module1: 具体的なモジュール名\n- module2: 詳細な説明付き",
                "timestamp": "2025-06-22T10:35:00"
            }
        ]
    }

def test_unified_interface_comprehensive(client):
    """統合テスト：ChatGPT応答→Claude評価→保存確認までを1つのテスト関数内に統合"""
    structure_id = "test_structure_001"
    
    # Mock responses
    chatgpt_response = {"content": '{"構成": {"項目": "内容"}}'}
    
    # MagicMockを使用してEvaluationResultの属性を正しく設定
    claude_eval_result = MagicMock()
    claude_eval_result.is_valid = True
    claude_eval_result.score = 0.85
    claude_eval_result.feedback = "良好です"
    claude_eval_result.details = {"評価スコア": 85}

    print(f"\n🔄 === 統合テスト開始: {structure_id} ===")
    
    # 全ての処理を1つのwithブロック内で実行（状態を維持）
    with patch("src.llm.controller.AIController.call", return_value=chatgpt_response), \
         patch("src.structure.evaluator.evaluate_structure_with", return_value=claude_eval_result), \
         patch("src.routes.unified_routes.evaluate_structure_with", return_value=claude_eval_result):
        
        # 1. ChatGPT応答をPOST
        print("📤 ChatGPT応答リクエスト送信...")
        response = client.post(
            f"/unified/{structure_id}/chat",
            json={"message": "ユーザーの質問"}
        )
        
        # 2. HTTPレスポンス確認
        assert response.status_code == 200, f"HTTPレスポンスエラー: {response.status_code}"
        print(f"✅ HTTPレスポンス: {response.status_code}")
        
        # 3. 保存されたmessages確認
        print("📁 保存された構成データ確認...")
        saved_structure = load_structure_by_id(structure_id)
        assert saved_structure is not None, "保存された構成データが見つかりません"
        
        messages = saved_structure.get("messages", [])
        print(f"📝 保存されたメッセージ数: {len(messages)}")
        print(f"📝 メッセージ内容: {json.dumps(messages, ensure_ascii=False, indent=2)}")
        
        # 4. メッセージ数確認（3件以上：user, ai, 評価）
        assert len(messages) >= 3, f"メッセージ数が不足: {len(messages)}件（期待値: 3件以上）"
        print(f"✅ メッセージ数確認: {len(messages)}件")
        
        # 5. メッセージ内容確認
        message_contents = [m.get("content", "") for m in messages]
        assert any("構成" in content for content in message_contents), "構成データが見つかりません"
        assert any("評価スコア" in str(content) for content in message_contents), "評価スコアが見つかりません"
        print("✅ メッセージ内容確認完了")
        
        # 6. メッセージ構造確認
        user_messages = [m for m in messages if m.get("role") == "user"]
        ai_messages = [m for m in messages if m.get("role") == "assistant"]
        evaluation_messages = [m for m in messages if m.get("type") == "claude_eval"]
        
        assert len(user_messages) >= 1, "ユーザーメッセージが見つかりません"
        assert len(ai_messages) >= 1, "AIメッセージが見つかりません"
        assert len(evaluation_messages) >= 1, "評価メッセージが見つかりません"
        print(f"✅ メッセージ構造確認: ユーザー{len(user_messages)}件, AI{len(ai_messages)}件, 評価{len(evaluation_messages)}件")

    print("🎉 === 統合テスト完了 ===")

def test_evaluation_completion_history_filtering_and_stats(client):
    """評価・補完履歴のフィルタリングと統計機能のテスト"""
    # テストデータ作成
    structure_id = "test_structure_001"
    structure = {
        "id": structure_id,
        "title": "テスト構成",
        "content": "テスト内容",
        "evaluations": [
            {"timestamp": "2024-01-01T10:00:00", "score": 0.8, "feedback": "良い評価"},
            {"timestamp": "2024-01-02T10:00:00", "score": 0.6, "feedback": "普通の評価"},
            {"timestamp": "2024-01-03T10:00:00", "score": 0.4, "feedback": "悪い評価"}
        ],
        "completions": [
            {"timestamp": "2024-01-01T11:00:00", "content": "短い補完"},
            {"timestamp": "2024-01-02T11:00:00", "content": "中程度の補完内容です"},
            {"timestamp": "2024-01-03T11:00:00", "content": "とても長い補完内容で、多くの文字を含んでいます"}
        ]
    }
    
    # 構造を保存
    save_structure(structure["id"], cast(StructureDict, structure))
    
    # 評価履歴ページのテスト
    response = client.get('/logs/evaluations')
    assert response.status_code == 200
    
    # 統計情報の確認
    assert '総件数'.encode('utf-8') in response.data
    assert '平均スコア'.encode('utf-8') in response.data
    assert '中央値スコア'.encode('utf-8') in response.data
    
    # フィルタボタンの確認
    assert b'data-filter="all"' in response.data
    assert b'data-filter="recent"' in response.data
    assert b'data-sort="desc"' in response.data
    assert b'data-sort="asc"' in response.data
    
    # 検索ボックスの確認
    assert 'タイトルで検索'.encode('utf-8') in response.data
    
    # 日付フィルタの確認
    assert b'fromDate' in response.data
    assert b'toDate' in response.data
    
    # 比較ボタンの確認
    assert b'/compare/' in response.data
    
    # 補完履歴ページのテスト
    response = client.get('/logs/completions')
    assert response.status_code == 200
    
    # 統計情報の確認
    assert '総件数'.encode('utf-8') in response.data
    assert '構成数'.encode('utf-8') in response.data
    assert '平均トークン数'.encode('utf-8') in response.data
    assert '中央値トークン数'.encode('utf-8') in response.data
    
    # フィルタボタンの確認
    assert b'data-filter="all"' in response.data
    assert b'data-filter="recent"' in response.data
    assert b'data-sort="desc"' in response.data
    assert b'data-sort="asc"' in response.data
    
    # 検索ボックスの確認
    assert 'タイトルで検索'.encode('utf-8') in response.data
    
    # 日付フィルタの確認
    assert b'fromDate' in response.data
    assert b'toDate' in response.data
    
    # 比較ボタンの確認
    assert b'/compare/' in response.data


def test_evaluation_completion_history_data_accuracy(client):
    """評価・補完履歴のデータ精度テスト"""
    # テストデータ作成
    structure_id = "test_structure_002"
    structure = {
        "id": structure_id,
        "title": "精度テスト構成",
        "content": "テスト内容",
        "evaluations": [
            {"timestamp": "2024-01-01T10:00:00", "score": 0.9, "feedback": "優秀"},
            {"timestamp": "2024-01-02T10:00:00", "score": 0.5, "feedback": "普通"},
            {"timestamp": "2024-01-03T10:00:00", "score": 0.1, "feedback": "改善必要"}
        ],
        "completions": [
            {"timestamp": "2024-01-01T11:00:00", "content": "短い"},
            {"timestamp": "2024-01-02T11:00:00", "content": "中程度の長さ"},
            {"timestamp": "2024-01-03T11:00:00", "content": "とても長い補完内容で、多くの文字を含んでいます"}
        ]
    }
    
    # 履歴ファイルを直接作成
    history_dir = os.path.join('logs', 'structure_history')
    os.makedirs(history_dir, exist_ok=True)
    
    # 履歴ファイルを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_file = os.path.join(history_dir, f'{structure_id}_{timestamp}.json')
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    
    # 評価履歴ページでデータ確認
    response = client.get('/logs/evaluations')
    assert response.status_code == 200
    
    # スコアの表示確認
    assert b'90.0' in response.data  # 0.9 * 100
    assert b'50.0' in response.data  # 0.5 * 100
    assert b'10.0' in response.data  # 0.1 * 100
    
    # フィードバックの表示確認
    assert '優秀'.encode('utf-8') in response.data
    assert '普通'.encode('utf-8') in response.data
    assert '改善必要'.encode('utf-8') in response.data
    
    # 補完履歴ページでデータ確認
    response = client.get('/logs/completions')
    assert response.status_code == 200
    
    # 補完内容の表示確認
    assert '短い'.encode('utf-8') in response.data
    assert '中程度の長さ'.encode('utf-8') in response.data
    assert 'とても長い補完内容'.encode('utf-8') in response.data


def test_evaluation_completion_history_empty_states(client):
    """評価・補完履歴の空状態テスト"""
    # 空の評価履歴ページ
    response = client.get('/logs/evaluations')
    assert response.status_code == 200
    assert '評価履歴が見つかりませんでした'.encode('utf-8') in response.data
    
    # 空の補完履歴ページ
    response = client.get('/logs/completions')
    assert response.status_code == 200
    assert '補完履歴が見つかりませんでした'.encode('utf-8') in response.data


def test_compare_page_functionality(client):
    """比較ページの機能テスト"""
    # テストデータ作成（複数の履歴）
    structure_id = "test_structure_003"
    
    # 1つ目の履歴
    structure1 = {
        "id": structure_id,
        "title": "初期構成",
        "content": "初期内容",
        "timestamp": "2024-01-01T10:00:00",
        "evaluations": [{"timestamp": "2024-01-01T10:00:00", "score": 0.7, "feedback": "初期評価"}],
        "completions": [{"timestamp": "2024-01-01T11:00:00", "content": "初期補完"}]
    }
    
    # 2つ目の履歴
    structure2 = {
        "id": structure_id,
        "title": "更新構成",
        "content": "更新内容",
        "timestamp": "2024-01-02T10:00:00",
        "evaluations": [{"timestamp": "2024-01-02T10:00:00", "score": 0.8, "feedback": "更新評価"}],
        "completions": [{"timestamp": "2024-01-02T11:00:00", "content": "更新補完"}]
    }
    
    # 履歴ファイルを直接作成
    history_dir = os.path.join('logs', 'structure_history')
    os.makedirs(history_dir, exist_ok=True)
    
    # 1つ目の履歴ファイルを作成
    history_file1 = os.path.join(history_dir, f'{structure_id}_20240101_100000.json')
    with open(history_file1, 'w', encoding='utf-8') as f:
        json.dump(structure1, f, ensure_ascii=False, indent=2)
    
    # 2つ目の履歴ファイルを作成
    history_file2 = os.path.join(history_dir, f'{structure_id}_20240102_100000.json')
    with open(history_file2, 'w', encoding='utf-8') as f:
        json.dump(structure2, f, ensure_ascii=False, indent=2)
    
    # 比較ページにアクセス
    response = client.get(f'/logs/compare/{structure_id}/2024-01-02T10:00:00')
    assert response.status_code == 200
    
    # 比較ページの要素確認
    assert '構成比較'.encode('utf-8') in response.data
    assert '現在の構成'.encode('utf-8') in response.data
    assert '前回の構成'.encode('utf-8') in response.data
    assert '評価履歴の比較'.encode('utf-8') in response.data
    assert '補完履歴の比較'.encode('utf-8') in response.data
    
    # データの表示確認
    assert '初期構成'.encode('utf-8') in response.data
    assert '更新構成'.encode('utf-8') in response.data
    assert '初期評価'.encode('utf-8') in response.data
    assert '更新評価'.encode('utf-8') in response.data
    assert '初期補完'.encode('utf-8') in response.data
    assert '更新補完'.encode('utf-8') in response.data


def test_compare_page_error_handling(client):
    """比較ページのエラーハンドリングテスト"""
    # 存在しない構成IDでの比較
    response = client.get('/logs/compare/nonexistent/2024-01-01T10:00:00')
    assert response.status_code == 200
    assert '指定されたタイムスタンプの構成が見つかりませんでした'.encode('utf-8') in response.data
    
    # 存在しないタイムスタンプでの比較
    structure_id = "test_structure_004"
    structure = {
        "id": structure_id,
        "title": "テスト構成",
        "content": "テスト内容",
        "timestamp": "2024-01-01T10:00:00"
    }
    
    # 履歴ファイルを作成
    history_dir = os.path.join('logs', 'structure_history')
    os.makedirs(history_dir, exist_ok=True)
    history_file = os.path.join(history_dir, f'{structure_id}_20240101_100000.json')
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    
    response = client.get(f'/logs/compare/{structure_id}/nonexistent-timestamp')
    assert response.status_code == 200
    assert '指定されたタイムスタンプの構成が見つかりませんでした'.encode('utf-8') in response.data

def test_unified_interface_with_restore(client, mock_load_structure, mock_load_evaluation_completion_history):
    """restoreパラメータ付きで統合インターフェースを表示するテスト"""
    # モックデータの設定
    mock_structure = {
        "id": "test_structure_001",
        "title": "テスト構成",
        "description": "テスト用の構成",
        "content": {"test": "data"},
        "messages": []
    }
    mock_load_structure.return_value = mock_structure
    
    # 履歴データのモック
    mock_histories = [
        {
            "timestamp": "2025-01-01T10:00:00",
            "evaluations": [{"score": 0.8, "feedback": "良い構成"}],
            "completions": [{"content": "補完内容"}]
        }
    ]
    mock_load_evaluation_completion_history.return_value = mock_histories
    
    # restore=0でアクセス
    response = client.get('/unified/test_structure_001?restore=0')
    
    assert response.status_code == 200
    assert 'テスト構成' in response.data.decode('utf-8')
    assert '履歴から復元しました' in response.data.decode('utf-8')
    
    # モックが正しく呼ばれたことを確認
    mock_load_structure.assert_called_once_with('test_structure_001')
    mock_load_evaluation_completion_history.assert_called_once_with('test_structure_001')

def test_save_structure_with_restore_note(client, mock_load_structure, mock_save_structure):
    """復元された構成の保存テスト"""
    # モックデータの設定
    mock_structure = {
        "id": "test_structure_001",
        "title": "テスト構成",
        "content": {"test": "data"},
        "messages": [],
        "evaluations": [{"score": 0.8, "feedback": "良い構成"}],
        "completions": [{"content": "補完内容"}]
    }
    mock_load_structure.return_value = mock_structure
    mock_save_structure.return_value = True
    
    # 復元された構成を保存
    response = client.post(
        '/unified/test_structure_001/save',
        json={
            "content": {"test": "updated_data"},
            "restore_note": True
        }
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] == True
    
    # モックが正しく呼ばれたことを確認
    mock_load_structure.assert_called_once_with('test_structure_001')
    mock_save_structure.assert_called_once()

def test_evaluate_claude_and_complete_gemini(client, mock_load_structure, mock_save_structure):
    """Claude評価・Gemini補完のAjaxルートのテスト"""
    # Claude評価
    mock_structure = {
        "id": "test_structure_001",
        "content": {"test": "data"},
        "messages": []
    }
    mock_load_structure.return_value = mock_structure
    mock_save_structure.return_value = True

    # Claude評価: provider=claude
    with patch('src.routes.unified_routes._evaluate_and_append_message') as mock_eval:
        mock_eval.side_effect = lambda s: s.setdefault('messages', []).append({"role": "assistant", "content": "Claude評価結果"})
        response = client.post('/unified/test_structure_001/evaluate?provider=claude', json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["message"]["content"] == "Claude評価結果"

    # Gemini補完: provider=gemini
    with patch('src.routes.unified_routes.apply_gemini_completion') as mock_gemini:
        def gemini_side_effect(s):
            s.setdefault('completions', []).append({"content": "Gemini補完内容"})
        mock_gemini.side_effect = gemini_side_effect
        response = client.post('/unified/test_structure_001/complete?provider=gemini', json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "Gemini補完" in data["message"]["content"]

    # エラーケース: 構造が見つからない
    mock_load_structure.return_value = None
    response = client.post('/unified/test_structure_001/evaluate?provider=claude', json={})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is False
    assert "構造が見つかりません" in data["error"] 

def test_gemini_completion_syntax_error_handling(client, mock_load_structure, mock_save_structure):
    """Gemini補完の構文エラー検出・ログ保存機能のテスト"""
    mock_structure = {
        "id": "test_structure_001",
        "content": {"test": "data"},
        "messages": []
    }
    mock_load_structure.return_value = mock_structure
    mock_save_structure.return_value = True

    # Gemini補完で構文エラーをシミュレート
    with patch('src.routes.unified_routes.apply_gemini_completion') as mock_gemini:
        def gemini_error_side_effect(s):
            # エラー情報を含むcompletionを返す
            error_completion = {
                "provider": "gemini",
                "content": "invalid json response",
                "timestamp": "2025-01-01T10:00:00",
                "status": "error",
                "error_message": "JSONDecodeError: Expecting property name enclosed in double quotes",
                "error_log_path": "logs/claude_gemini_diff/test_structure_001_gemini_error.json"
            }
            s.setdefault('completions', []).append(error_completion)
            return error_completion
        mock_gemini.side_effect = gemini_error_side_effect
        
        response = client.post('/unified/test_structure_001/complete?provider=gemini', json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # エラーレスポンスの確認
        assert data["success"] is False
        assert "構文エラーが検出されました" in data["error"]
        assert data["error_details"]["error_message"] == "JSONDecodeError: Expecting property name enclosed in double quotes"
        assert data["error_details"]["error_log_path"] == "logs/claude_gemini_diff/test_structure_001_gemini_error.json"
        assert data["message"]["type"] == "gemini_error"

def test_gemini_completion_with_claude_repair(client, mock_load_structure, mock_save_structure):
    """Gemini構文エラー時のClaude自動修復機能のテスト"""
    mock_structure = {
        "id": "test_structure_001",
        "content": {"test": "data"},
        "messages": []
    }
    mock_load_structure.return_value = mock_structure
    mock_save_structure.return_value = True

    # Gemini補完で構文エラー + Claude修復成功をシミュレート
    with patch('src.routes.unified_routes.apply_gemini_completion') as mock_gemini:
        def gemini_repair_side_effect(s):
            # Claude修復結果を含むcompletionを返す
            repair_completion = {
                "provider": "gemini",
                "content": "invalid json response",
                "timestamp": "2025-01-01T10:00:00",
                "status": "error",
                "error_message": "JSONDecodeError: Expecting property name enclosed in double quotes",
                "error_log_path": "logs/claude_gemini_diff/test_structure_001_gemini_error.json",
                "fallback": {
                    "provider": "claude",
                    "content": {"repaired": "json", "structure": "data"},
                    "timestamp": "2025-01-01T10:01:00",
                    "repair_method": "claude_auto_repair"
                }
            }
            s.setdefault('completions', []).append(repair_completion)
            return repair_completion
        mock_gemini.side_effect = gemini_repair_side_effect
        
        response = client.post('/unified/test_structure_001/complete?provider=gemini', json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # エラーレスポンスだがClaude修復結果が含まれていることを確認
        assert data["success"] is False
        assert "構文エラーが検出されました" in data["error"]
        assert "completion" in data
        assert data["completion"]["fallback"]["provider"] == "claude"
        assert data["completion"]["fallback"]["repair_method"] == "claude_auto_repair"
        assert data["completion"]["fallback"]["content"] == {"repaired": "json", "structure": "data"}

def test_claude_repair_integration(client, mock_load_structure, mock_save_structure):
    """Claude修復機能の統合テスト"""
    mock_structure = {
        "id": "test_structure_001",
        "content": {"test": "data"},
        "messages": []
    }
    mock_load_structure.return_value = mock_structure
    mock_save_structure.return_value = True

    # apply_gemini_completionの実際の動作をテスト
    with patch('src.llm.controller.AIController.generate_response') as mock_generate:
        # Geminiが不正なJSONを返す
        mock_generate.return_value = "invalid json: { title: unquoted_key }"
        
        with patch('src.structure.feedback.call_claude') as mock_claude:
            # Claudeが修復されたJSONを返す
            mock_claude.return_value = '{"title": "quoted_key", "content": "valid_json"}'
            
            with patch('src.utils.files.extract_json_part') as mock_extract:
                # 最初のextract_json_partは失敗（Geminiの不正JSON）
                # 2回目のextract_json_partは成功（Claudeの修復結果）
                mock_extract.side_effect = [None, {"title": "quoted_key", "content": "valid_json"}]
                
                response = client.post('/unified/test_structure_001/complete?provider=gemini', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Claude修復が実行されたことを確認
                assert data["success"] is False  # Geminiは失敗
                assert "completion" in data
                assert data["completion"]["fallback"]["provider"] == "claude"
                assert data["completion"]["fallback"]["repair_method"] == "claude_auto_repair"
                
                # ログファイルが作成されることを確認
                assert "error_log_path" in data["error_details"]

def test_claude_repair_api(client, mock_load_structure, mock_save_structure, tmp_path):
    """Claude構文修復APIのテスト"""
    # テスト用のエラーログファイルを作成
    error_log_data = {
        "structure_id": "test_structure_001",
        "timestamp": "2025-01-01T10:00:00",
        "error_type": "gemini_syntax_error",
        "error_message": "JSONDecodeError: Expecting property name enclosed in double quotes",
        "gemini_raw_response": "invalid json: { title: unquoted_key }",
        "original_content": {
            "title": "テスト構成",
            "content": {"test": "data"}
        }
    }
    
    # ログディレクトリを作成
    log_dir = tmp_path / "logs" / "claude_gemini_diff"
    log_dir.mkdir(parents=True)
    
    # エラーログファイルを保存
    error_log_path = log_dir / "test_structure_001_gemini_error.json"
    with open(error_log_path, 'w', encoding='utf-8') as f:
        json.dump(error_log_data, f, ensure_ascii=False, indent=2)
    
    # パスをモック
    with patch('os.path.join') as mock_join:
        mock_join.return_value = str(error_log_path)
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('src.structure.feedback.call_claude') as mock_claude:
                # Claudeが修復されたJSONを返す
                mock_claude.return_value = '{"title": "quoted_key", "content": {"test": "data"}}'
                
                with patch('src.utils.files.extract_json_part') as mock_extract:
                    mock_extract.return_value = {"title": "quoted_key", "content": {"test": "data"}}
                    
                    with patch('src.routes.unified_routes.save_structure') as mock_save:
                        mock_save.return_value = True
                        
                        # 修復APIを呼び出し
                        response = client.post('/unified/repair_structure/test_structure_001', json={
                            'timestamp': '2025-01-01T10:00:00',
                            'structure_id': 'test_structure_001'
                        })
                        
                        assert response.status_code == 200
                        data = json.loads(response.data)
                        
                        # 修復成功の確認
                        assert data["success"] is True
                        assert "repaired_structure_id" in data
                        assert "repaired_content" in data
                        assert "original_content" in data
                        assert data["repaired_content"]["title"] == "quoted_key"
                        assert data["original_content"]["title"] == "テスト構成"

def test_claude_repair_api_error_log_not_found(client):
    """エラーログファイルが見つからない場合のテスト"""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        
        response = client.post('/unified/repair_structure/test_structure_001', json={
            'timestamp': '2025-01-01T10:00:00',
            'structure_id': 'test_structure_001'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is False
        assert "エラーログファイルが見つかりません" in data["error"]

def test_claude_repair_api_claude_no_response(client, tmp_path):
    """Claudeからの応答がない場合のテスト"""
    # テスト用のエラーログファイルを作成
    error_log_data = {
        "structure_id": "test_structure_001",
        "error_message": "JSONDecodeError",
        "gemini_raw_response": "invalid json",
        "original_content": {"test": "data"}
    }
    
    log_dir = tmp_path / "logs" / "claude_gemini_diff"
    log_dir.mkdir(parents=True)
    error_log_path = log_dir / "test_structure_001_gemini_error.json"
    
    with open(error_log_path, 'w', encoding='utf-8') as f:
        json.dump(error_log_data, f, ensure_ascii=False, indent=2)
    
    with patch('os.path.join') as mock_join:
        mock_join.return_value = str(error_log_path)
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('src.structure.feedback.call_claude') as mock_claude:
                # Claudeが空の応答を返す
                mock_claude.return_value = ""
                
                response = client.post('/unified/repair_structure/test_structure_001', json={
                    'timestamp': '2025-01-01T10:00:00',
                    'structure_id': 'test_structure_001'
                })
                
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data["success"] is False
                assert "Claudeからの応答がありませんでした" in data["error"]

def test_claude_repair_api_invalid_json_response(client, tmp_path):
    """Claudeの応答から有効なJSONが抽出できない場合のテスト"""
    # テスト用のエラーログファイルを作成
    error_log_data = {
        "structure_id": "test_structure_001",
        "error_message": "JSONDecodeError",
        "gemini_raw_response": "invalid json",
        "original_content": {"test": "data"}
    }
    
    log_dir = tmp_path / "logs" / "claude_gemini_diff"
    log_dir.mkdir(parents=True)
    error_log_path = log_dir / "test_structure_001_gemini_error.json"
    
    with open(error_log_path, 'w', encoding='utf-8') as f:
        json.dump(error_log_data, f, ensure_ascii=False, indent=2)
    
    with patch('os.path.join') as mock_join:
        mock_join.return_value = str(error_log_path)
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('src.structure.feedback.call_claude') as mock_claude:
                # Claudeが無効なJSONを返す
                mock_claude.return_value = "This is not valid JSON"
                
                with patch('src.utils.files.extract_json_part') as mock_extract:
                    mock_extract.return_value = None
                    
                    response = client.post('/unified/repair_structure/test_structure_001', json={
                        'timestamp': '2025-01-01T10:00:00',
                        'structure_id': 'test_structure_001'
                    })
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    
                    assert data["success"] is False
                    assert "No JSON object found in text" in data["error"]
                    assert data["claude_output"] == "This is not valid JSON" 