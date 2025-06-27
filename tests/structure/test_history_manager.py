"""
履歴管理機能のテスト
"""

import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from src.structure.history_manager import (
    save_structure_history,
    load_structure_history,
    get_history_summary,
    cleanup_old_history
)


class TestHistoryManager:
    """履歴管理機能のテストクラス"""
    
    @pytest.fixture
    def temp_history_dir(self):
        """一時的な履歴ディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        history_dir = Path(temp_dir) / "data" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        
        # 一時的に履歴ディレクトリを変更
        original_cwd = Path.cwd()
        try:
            # テスト用の一時ディレクトリに移動
            import os
            os.chdir(temp_dir)
            yield temp_dir
        finally:
            # 元のディレクトリに戻る
            os.chdir(original_cwd)
            # 一時ディレクトリを削除
            shutil.rmtree(temp_dir)
    
    def test_save_structure_history_new_file(self, temp_history_dir):
        """新しい構造の履歴を保存するテスト"""
        structure_id = "test_structure_001"
        role = "user"
        source = "save_structure"
        content = '{"title": "テスト構造", "content": "テスト内容"}'
        module_id = "test_module"
        
        # 履歴を保存
        result = save_structure_history(structure_id, role, source, content, module_id)
        
        # 保存が成功したことを確認
        assert result is True
        
        # ファイルが作成されたことを確認
        history_file = Path("data/history") / f"{structure_id}.json"
        assert history_file.exists()
        
        # ファイル内容を確認
        with history_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["structure_id"] == structure_id
        assert data["module_id"] == module_id
        assert len(data["history"]) == 1
        
        history_entry = data["history"][0]
        assert history_entry["role"] == role
        assert history_entry["source"] == source
        assert history_entry["content"] == content
        assert "timestamp" in history_entry
    
    def test_save_structure_history_existing_file(self, temp_history_dir):
        """既存の構造の履歴を追加するテスト"""
        structure_id = "test_structure_002"
        
        # 最初の履歴を保存
        save_structure_history(
            structure_id, "user", "save_structure", 
            '{"title": "初期構造"}', "module1"
        )
        
        # 2番目の履歴を保存
        save_structure_history(
            structure_id, "claude", "structure_evaluation", 
            '{"score": 0.8, "feedback": "良い構造です"}', "module1"
        )
        
        # 履歴を読み込み
        history_data = load_structure_history(structure_id)
        
        # 履歴が2つあることを確認
        assert history_data is not None
        assert len(history_data["history"]) == 2
        
        # 最初の履歴を確認
        first_entry = history_data["history"][0]
        assert first_entry["role"] == "user"
        assert first_entry["source"] == "save_structure"
        
        # 2番目の履歴を確認
        second_entry = history_data["history"][1]
        assert second_entry["role"] == "claude"
        assert second_entry["source"] == "structure_evaluation"
    
    def test_load_structure_history_not_found(self, temp_history_dir):
        """存在しない構造の履歴を読み込むテスト"""
        structure_id = "non_existent_structure"
        
        # 履歴を読み込み
        history_data = load_structure_history(structure_id)
        
        # Noneが返されることを確認
        assert history_data is None
    
    def test_get_history_summary(self, temp_history_dir):
        """履歴サマリーを取得するテスト"""
        structure_id = "test_structure_003"
        
        # 複数の履歴を保存
        save_structure_history(structure_id, "user", "save_structure", "content1")
        save_structure_history(structure_id, "claude", "structure_evaluation", "content2")
        save_structure_history(structure_id, "gemini", "structure_completion", "content3")
        
        # サマリーを取得
        summary = get_history_summary(structure_id)
        
        # サマリーの内容を確認
        assert summary["structure_id"] == structure_id
        assert summary["total_entries"] == 3
        assert summary["last_updated"] is not None
        assert "user" in summary["roles"]
        assert "claude" in summary["roles"]
        assert "gemini" in summary["roles"]
        assert "save_structure" in summary["sources"]
        assert "structure_evaluation" in summary["sources"]
        assert "structure_completion" in summary["sources"]
    
    def test_get_history_summary_not_found(self, temp_history_dir):
        """存在しない構造の履歴サマリーを取得するテスト"""
        structure_id = "non_existent_structure"
        
        # サマリーを取得
        summary = get_history_summary(structure_id)
        
        # デフォルト値が返されることを確認
        assert summary["structure_id"] == structure_id
        assert summary["total_entries"] == 0
        assert summary["last_updated"] is None
        assert summary["roles"] == []
        assert summary["sources"] == []
    
    def test_save_structure_history_invalid_json(self, temp_history_dir):
        """無効なJSONで履歴保存をテスト"""
        structure_id = "test_structure_004"
        
        # 無効なJSONで履歴を保存
        result = save_structure_history(
            structure_id, "user", "save_structure", 
            "invalid json content"
        )
        
        # 保存が成功することを確認（JSONの妥当性はチェックしない）
        assert result is True
        
        # ファイルが作成されたことを確認
        history_file = Path("data/history") / f"{structure_id}.json"
        assert history_file.exists()
    
    def test_save_structure_history_empty_content(self, temp_history_dir):
        """空の内容で履歴保存をテスト"""
        structure_id = "test_structure_005"
        
        # 空の内容で履歴を保存
        result = save_structure_history(
            structure_id, "user", "save_structure", ""
        )
        
        # 保存が成功することを確認
        assert result is True
        
        # 履歴を読み込み
        history_data = load_structure_history(structure_id)
        
        # 空の内容が保存されていることを確認
        assert history_data is not None
        assert history_data["history"][0]["content"] == ""
    
    def test_save_structure_history_special_characters(self, temp_history_dir):
        """特殊文字を含む内容で履歴保存をテスト"""
        structure_id = "test_structure_006"
        content = '{"title": "テスト構造", "description": "日本語と特殊文字: あいうえお & < > \" \'"}'
        
        # 特殊文字を含む内容で履歴を保存
        result = save_structure_history(
            structure_id, "user", "save_structure", content
        )
        
        # 保存が成功することを確認
        assert result is True
        
        # 履歴を読み込み
        history_data = load_structure_history(structure_id)
        
        # 特殊文字が正しく保存されていることを確認
        assert history_data is not None
        assert history_data["history"][0]["content"] == content 