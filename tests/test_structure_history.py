"""
構造履歴保存機能のテスト
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.structure.history import (
    save_structure_history,
    load_structure_history,
    get_structure_history_by_provider,
    get_latest_structure_history,
    compare_structure_history,
    cleanup_old_structure_history
)


class TestStructureHistory:
    """構造履歴機能のテストクラス"""
    
    def setup_method(self):
        """テスト前の準備"""
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        self.original_data_dir = os.environ.get('AIDEX_DATA_DIR')
        os.environ['AIDEX_DATA_DIR'] = self.test_dir
        # テスト用の構造履歴ディレクトリを作成
        self.history_dir = os.path.join(self.test_dir, "structure_history")
        os.makedirs(self.history_dir, exist_ok=True)
    
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if self.original_data_dir is not None:
            os.environ['AIDEX_DATA_DIR'] = self.original_data_dir
        else:
            if 'AIDEX_DATA_DIR' in os.environ:
                del os.environ['AIDEX_DATA_DIR']
    
    def test_save_structure_history_success(self):
        """履歴保存の成功テスト"""
        structure_id = "test_structure_001"
        test_structure = {
            "title": "テスト構成",
            "modules": {"module1": {"title": "テストモジュール"}}
        }
        
        # 履歴保存を実行
        result = save_structure_history(
            structure_id=structure_id,
            structure=test_structure,
            provider="claude",
            score=0.85,
            comment="テスト評価"
        )
        
        # 結果を検証
        assert result is True
        
        # ファイルが作成されているか確認
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        assert os.path.exists(file_path)
        
        # ファイル内容を確認
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # JSONL形式で正しく保存されているか確認
            history_entry = json.loads(lines[0])
            assert history_entry["timestamp"] is not None
            assert history_entry["role"] == "assistant"
            assert history_entry["source"] == "claude"
            assert history_entry["score"] == 0.85
            assert history_entry["comment"] == "テスト評価"
            assert history_entry["content"] == test_structure
    
    def test_save_structure_history_multiple_entries(self):
        """複数エントリの履歴保存テスト"""
        structure_id = "test_structure_002"
        
        # 複数の履歴を保存
        for i in range(3):
            test_structure = {
                "title": f"テスト構成{i}",
                "modules": {f"module{i}": {"title": f"テストモジュール{i}"}}
            }
            
            result = save_structure_history(
                structure_id=structure_id,
                structure=test_structure,
                provider="claude" if i % 2 == 0 else "gemini",
                score=0.8 + i * 0.05,
                comment=f"テスト評価{i}"
            )
            assert result is True
        
        # ファイル内容を確認
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 3
            
            # 各エントリが正しく保存されているか確認
            for i, line in enumerate(lines):
                history_entry = json.loads(line)
                assert history_entry["timestamp"] is not None
                assert history_entry["role"] == "assistant"
                assert history_entry["source"] in ["claude", "gemini"]
                assert history_entry["content"]["title"] == f"テスト構成{i}"
    
    def test_load_structure_history(self):
        """履歴読み込みのテスト"""
        structure_id = "test_structure_003"
        
        # テストデータを準備（timestampを明示的にずらす）
        test_entries = []
        base_time = datetime.now()
        for i in range(3):
            test_structure = {
                "title": f"テスト構成{i}",
                "modules": {f"module{i}": {"title": f"テストモジュール{i}"}}
            }
            # 新しい順になるようtimestampをずらす（i=2が最新）
            timestamp = base_time + timedelta(seconds=i)
            test_entries.append({
                "timestamp": timestamp.isoformat(),
                "role": "assistant",
                "source": "claude" if i % 2 == 0 else "gemini",
                "score": 0.8 + i * 0.05,
                "comment": f"テスト評価{i}",
                "content": test_structure
            })
        
        # テストファイルを作成
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in test_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # 履歴読み込みを実行
        history_list = load_structure_history(structure_id)
        
        # 結果を検証
        assert len(history_list) == 3
        assert history_list[0]["content"]["title"] == "テスト構成2"  # 新しい順
        assert history_list[1]["content"]["title"] == "テスト構成1"
        assert history_list[2]["content"]["title"] == "テスト構成0"
    
    def test_get_structure_history_by_provider(self):
        """プロバイダー別履歴取得のテスト"""
        structure_id = "test_structure_004"
        
        # テストデータを準備（Claude 2件、Gemini 1件）
        test_entries = [
            {"source": "claude", "content": {"title": "Claude構成1"}},
            {"source": "gemini", "content": {"title": "Gemini構成1"}},
            {"source": "claude", "content": {"title": "Claude構成2"}}
        ]
        
        # テストファイルを作成
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in test_entries:
                full_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "role": "assistant",
                    "source": entry["source"],
                    "content": entry["content"]
                }
                f.write(json.dumps(full_entry, ensure_ascii=False) + "\n")
        
        # Claude履歴を取得
        claude_history = get_structure_history_by_provider(structure_id, "claude")
        assert len(claude_history) == 2
        assert all(entry["source"] == "claude" for entry in claude_history)
        
        # Gemini履歴を取得
        gemini_history = get_structure_history_by_provider(structure_id, "gemini")
        assert len(gemini_history) == 1
        assert all(entry["source"] == "gemini" for entry in gemini_history)
    
    def test_get_latest_structure_history(self):
        """最新履歴取得のテスト"""
        structure_id = "test_structure_005"
        
        # テストデータを準備（timestampを明示的にずらす）
        base_time = datetime.now()
        test_entries = [
            {
                "source": "claude", 
                "content": {"title": "古い構成"},
                "timestamp": base_time.isoformat()
            },
            {
                "source": "gemini", 
                "content": {"title": "新しい構成"},
                "timestamp": (base_time + timedelta(seconds=10)).isoformat()
            }
        ]
        
        # テストファイルを作成
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in test_entries:
                full_entry = {
                    "timestamp": entry["timestamp"],
                    "role": "assistant",
                    "source": entry["source"],
                    "content": entry["content"]
                }
                f.write(json.dumps(full_entry, ensure_ascii=False) + "\n")
        
        # 最新履歴を取得（全プロバイダー）
        latest = get_latest_structure_history(structure_id)
        assert latest["content"]["title"] == "新しい構成"
        
        # Claudeの最新履歴を取得
        latest_claude = get_latest_structure_history(structure_id, "claude")
        assert latest_claude["content"]["title"] == "古い構成"
    
    def test_compare_structure_history(self):
        """履歴比較のテスト"""
        structure_id = "test_structure_006"
        
        # テストデータを準備
        test_entries = [
            {
                "source": "claude",
                "content": {
                    "title": "構成A",
                    "modules": {"module1": {"title": "モジュール1"}}
                }
            },
            {
                "source": "claude",
                "content": {
                    "title": "構成B",
                    "modules": {
                        "module1": {"title": "モジュール1"},
                        "module2": {"title": "モジュール2"}
                    }
                }
            }
        ]
        
        # テストファイルを作成
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in test_entries:
                full_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "role": "assistant",
                    "source": entry["source"],
                    "content": entry["content"]
                }
                f.write(json.dumps(full_entry, ensure_ascii=False) + "\n")
        
        # 履歴比較を実行
        diff_result = compare_structure_history(structure_id, 0, 1)
        
        # 結果を検証
        assert diff_result is not None
        assert diff_result["structure_id"] == structure_id
        assert "differences" in diff_result
        assert "title" in diff_result["differences"]
        assert "module_count" in diff_result["differences"]
    
    def test_cleanup_old_structure_history(self):
        """古い履歴ファイル削除のテスト"""
        # 古いファイルを作成
        old_file = os.path.join(self.history_dir, "old_structure.jsonl")
        with open(old_file, "w") as f:
            f.write("old content")
        
        # ファイルの更新時刻を古くする
        old_timestamp = datetime.now().timestamp() - (31 * 24 * 60 * 60)  # 31日前
        os.utime(old_file, (old_timestamp, old_timestamp))
        
        # 新しいファイルを作成
        new_file = os.path.join(self.history_dir, "new_structure.jsonl")
        with open(new_file, "w") as f:
            f.write("new content")
        
        # 古いファイル削除を実行
        deleted_count = cleanup_old_structure_history(days_to_keep=30)
        
        # 結果を検証
        assert deleted_count == 1
        assert not os.path.exists(old_file)
        assert os.path.exists(new_file)
    
    def test_save_structure_history_with_none_values(self):
        """None値を含む履歴保存のテスト"""
        structure_id = "test_structure_007"
        test_structure = {"title": "テスト構成"}
        
        # None値を含む履歴保存を実行
        result = save_structure_history(
            structure_id=structure_id,
            structure=test_structure,
            provider="gemini",
            score=None,
            comment=""
        )
        
        # 結果を検証
        assert result is True
        
        # ファイル内容を確認
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "r", encoding="utf-8") as f:
            history_entry = json.loads(f.readline())
            assert history_entry["timestamp"] is not None
            assert history_entry["role"] == "assistant"
            assert history_entry["source"] == "gemini"
            assert history_entry["content"] == test_structure
            # scoreフィールドはNoneの場合追加されない
            assert "score" not in history_entry
    
    def test_load_structure_history_empty_file(self):
        """空の履歴ファイル読み込みのテスト"""
        structure_id = "test_structure_008"
        
        # 空のファイルを作成
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "w") as f:
            pass
        
        # 履歴読み込みを実行
        history_list = load_structure_history(structure_id)
        
        # 結果を検証
        assert len(history_list) == 0
    
    def test_load_structure_history_invalid_json(self):
        """無効なJSONを含む履歴ファイル読み込みのテスト"""
        structure_id = "test_structure_009"
        
        # 無効なJSONを含むファイルを作成
        file_path = os.path.join(self.history_dir, f"{structure_id}.jsonl")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('{"valid": "json"}\n')
            f.write('invalid json line\n')
            f.write('{"another": "valid"}\n')
        
        # 履歴読み込みを実行
        history_list = load_structure_history(structure_id)
        
        # 結果を検証（有効なJSONのみ読み込まれる）
        assert len(history_list) == 2
        # 順序は保持される（timestampがないため）
        assert history_list[0]["valid"] == "json"
        assert history_list[1]["another"] == "valid"


if __name__ == "__main__":
    pytest.main([__file__]) 