import json
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

def test_unified_structure_history_success(client, tmp_path):
    """履歴一覧表示の成功テスト"""
    # テスト用の履歴データを作成
    history_data = [
        {
            "id": "history_001",
            "structure_id": "test_structure_001",
            "timestamp": "2025-01-01T10:00:00",
            "role": "user",
            "content": {"title": "初期構成", "data": "test1"}
        },
        {
            "id": "history_002", 
            "structure_id": "test_structure_001",
            "timestamp": "2025-01-01T11:00:00",
            "role": "assistant",
            "content": {"title": "更新構成", "data": "test2", "new_field": "added"}
        }
    ]
    
    # 履歴ディレクトリを作成
    history_dir = tmp_path / "data" / "history"
    history_dir.mkdir(parents=True)
    
    # 履歴ファイルを保存
    for history in history_data:
        with open(history_dir / f"{history['id']}.json", 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    with patch('src.structure.history.HISTORY_DIR', str(history_dir)):
        with patch('src.routes.unified_routes.generate_diff_html') as mock_diff:
            mock_diff.return_value = '<span class="diff-test">テスト差分</span>'
            
            response = client.get('/unified/test_structure_001/history')
            
            assert response.status_code == 200
            assert '構成履歴一覧' in response.data.decode('utf-8')
            assert 'history_001' in response.data.decode('utf-8')
            assert 'history_002' in response.data.decode('utf-8')

def test_unified_structure_history_empty(client):
    """履歴が存在しない場合のテスト"""
    with patch('src.structure.history.get_structure_history') as mock_get:
        mock_get.return_value = []
        
        response = client.get('/unified/test_structure_001/history')
        
        assert response.status_code == 200
        assert '履歴がありません' in response.data.decode('utf-8')

def test_unified_structure_history_error(client):
    """履歴取得エラーのテスト"""
    with patch('src.structure.history.get_structure_history') as mock_get:
        mock_get.side_effect = Exception("履歴取得エラー")
        
        response = client.get('/unified/test_structure_001/history')
        
        assert response.status_code == 200
        assert 'エラー' in response.data.decode('utf-8')

def test_restore_structure_from_history_success(client, tmp_path):
    """履歴からの復元成功テスト"""
    # テスト用の履歴データ
    history_data = {
        "id": "history_001",
        "structure_id": "test_structure_001", 
        "content": {"title": "復元構成", "data": "restored"}
    }
    
    # 履歴ディレクトリを作成
    history_dir = tmp_path / "data" / "history"
    history_dir.mkdir(parents=True)
    
    # 履歴ファイルを保存
    with open(history_dir / "history_001.json", 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    
    # 構造ファイルディレクトリを作成
    structure_dir = tmp_path / "data"
    structure_dir.mkdir(parents=True)
    
    # 既存の構造ファイルを作成
    existing_structure = {"title": "既存構成", "data": "existing"}
    with open(structure_dir / "test_structure_001.json", 'w', encoding='utf-8') as f:
        json.dump(existing_structure, f, ensure_ascii=False, indent=2)
    
    with patch('src.structure.history.HISTORY_DIR', str(history_dir)):
        with patch('src.structure.history.restore_structure_from_history') as mock_restore:
            mock_restore.return_value = True
            
            response = client.post('/unified/restore_structure/test_structure_001/history_001')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

def test_restore_structure_from_history_not_found(client):
    """履歴が見つからない場合の復元テスト"""
    with patch('src.structure.history.restore_structure_from_history') as mock_restore:
        mock_restore.return_value = False
        
        response = client.post('/unified/restore_structure/test_structure_001/nonexistent')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "履歴が見つかりません" in data["error"]

def test_restore_structure_from_history_error(client):
    """復元処理エラーのテスト"""
    with patch('src.structure.history.restore_structure_from_history') as mock_restore:
        mock_restore.side_effect = Exception("復元エラー")
        
        response = client.post('/unified/restore_structure/test_structure_001/history_001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "復元エラー" in data["error"]

def test_diff_generation_with_deepdiff(client, tmp_path):
    """DeepDiffを使用した差分生成のテスト"""
    # テスト用の履歴データ（差分がある場合）
    history_data = [
        {
            "id": "history_001",
            "structure_id": "test_structure_001",
            "content": {"title": "初期", "data": "old"}
        },
        {
            "id": "history_002",
            "structure_id": "test_structure_001", 
            "content": {"title": "更新", "data": "new", "added": "value"}
        }
    ]
    
    history_dir = tmp_path / "data" / "history"
    history_dir.mkdir(parents=True)
    
    for history in history_data:
        with open(history_dir / f"{history['id']}.json", 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    with patch('src.structure.history.HISTORY_DIR', str(history_dir)):
        with patch('src.routes.unified_routes.generate_diff_html') as mock_diff:
            mock_diff.return_value = '<div class="diff-section">テスト差分</div>'
            
            response = client.get('/unified/test_structure_001/history')
            
            assert response.status_code == 200
            # 差分が生成されていることを確認
            response_text = response.data.decode('utf-8')
            assert 'diff-section' in response_text or 'diff-block' in response_text

def test_diff_generation_without_deepdiff(client, tmp_path):
    """DeepDiffが利用できない場合の差分生成テスト"""
    # DeepDiffのインポートを失敗させる
    with patch('src.routes.unified_routes.DeepDiff', side_effect=ImportError):
        history_data = [
            {
                "id": "history_001",
                "structure_id": "test_structure_001",
                "content": {"title": "初期", "data": "old"}
            },
            {
                "id": "history_002",
                "structure_id": "test_structure_001",
                "content": {"title": "更新", "data": "new"}
            }
        ]
        
        history_dir = tmp_path / "data" / "history"
        history_dir.mkdir(parents=True)
        
        for history in history_data:
            with open(history_dir / f"{history['id']}.json", 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        
        with patch('src.structure.history.HISTORY_DIR', str(history_dir)):
            with patch('src.routes.unified_routes.generate_simple_diff_html') as mock_simple_diff:
                mock_simple_diff.return_value = '<div class="diff-simple">簡易差分</div>'
                
                response = client.get('/unified/test_structure_001/history')
                
                assert response.status_code == 200
                # 簡易差分が生成されていることを確認
                response_text = response.data.decode('utf-8')
                assert 'diff-simple' in response_text or 'diff-block' in response_text 