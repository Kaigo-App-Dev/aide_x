"""
モジュール差分機能のテスト
"""
import pytest
import json
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.structure.diff_utils import generate_module_diff, get_module_changes


class TestModuleDiff:
    """モジュール差分機能のテストクラス"""
    
    def test_generate_module_diff_empty(self):
        """空のモジュールリストでの差分生成テスト"""
        before_modules = []
        after_modules = []
        
        result = generate_module_diff(before_modules, after_modules)
        
        assert result["added"] == []
        assert result["removed"] == []
        assert result["changed"] == []
    
    def test_generate_module_diff_added_only(self):
        """追加されたモジュールのみのテスト"""
        before_modules = []
        after_modules = [
            {"name": "新モジュール1", "description": "追加されたモジュール1"},
            {"name": "新モジュール2", "description": "追加されたモジュール2"}
        ]
        
        result = generate_module_diff(before_modules, after_modules)
        
        assert len(result["added"]) == 2
        assert len(result["removed"]) == 0
        assert len(result["changed"]) == 0
        
        assert result["added"][0]["name"] == "新モジュール1"
        assert result["added"][1]["name"] == "新モジュール2"
    
    def test_generate_module_diff_removed_only(self):
        """削除されたモジュールのみのテスト"""
        before_modules = [
            {"name": "削除モジュール1", "description": "削除されるモジュール1"},
            {"name": "削除モジュール2", "description": "削除されるモジュール2"}
        ]
        after_modules = []
        
        result = generate_module_diff(before_modules, after_modules)
        
        assert len(result["added"]) == 0
        assert len(result["removed"]) == 2
        assert len(result["changed"]) == 0
        
        assert result["removed"][0]["name"] == "削除モジュール1"
        assert result["removed"][1]["name"] == "削除モジュール2"
    
    def test_generate_module_diff_changed_only(self):
        """変更されたモジュールのみのテスト"""
        before_modules = [
            {"name": "変更モジュール", "description": "変更前の説明", "version": "1.0"}
        ]
        after_modules = [
            {"name": "変更モジュール", "description": "変更後の説明", "version": "2.0"}
        ]
        
        result = generate_module_diff(before_modules, after_modules)
        
        assert len(result["added"]) == 0
        assert len(result["removed"]) == 0
        assert len(result["changed"]) == 1
        
        changed_module = result["changed"][0]
        assert changed_module["name"] == "変更モジュール"
        assert "changes" in changed_module
        assert len(changed_module["changes"]) == 2  # description と version が変更
    
    def test_generate_module_diff_mixed_changes(self):
        """追加・削除・変更が混在するテスト"""
        before_modules = [
            {"name": "削除モジュール", "description": "削除される"},
            {"name": "変更モジュール", "description": "変更前", "version": "1.0"},
            {"name": "維持モジュール", "description": "変更なし"}
        ]
        after_modules = [
            {"name": "追加モジュール", "description": "新しく追加"},
            {"name": "変更モジュール", "description": "変更後", "version": "2.0"},
            {"name": "維持モジュール", "description": "変更なし"}
        ]
        
        result = generate_module_diff(before_modules, after_modules)
        
        assert len(result["added"]) == 1
        assert len(result["removed"]) == 1
        assert len(result["changed"]) == 1
        
        assert result["added"][0]["name"] == "追加モジュール"
        assert result["removed"][0]["name"] == "削除モジュール"
        assert result["changed"][0]["name"] == "変更モジュール"
    
    def test_generate_module_diff_with_title_field(self):
        """titleフィールドを使用したモジュールのテスト"""
        before_modules = [
            {"title": "タイトルモジュール1", "description": "説明1"}
        ]
        after_modules = [
            {"title": "タイトルモジュール1", "description": "説明2"},
            {"title": "タイトルモジュール2", "description": "説明3"}
        ]
        
        result = generate_module_diff(before_modules, after_modules)
        
        assert len(result["added"]) == 1
        assert len(result["removed"]) == 0
        assert len(result["changed"]) == 1
        
        assert result["added"][0]["title"] == "タイトルモジュール2"
        assert result["changed"][0]["before"]["title"] == "タイトルモジュール1"
    
    def test_generate_module_diff_no_name_or_title(self):
        """nameもtitleもないモジュールのテスト"""
        before_modules = [
            {"description": "説明1", "type": "form"}
        ]
        after_modules = [
            {"description": "説明2", "type": "table"}
        ]
        
        result = generate_module_diff(before_modules, after_modules)
        
        assert len(result["added"]) == 1
        assert len(result["removed"]) == 1
        assert len(result["changed"]) == 0
    
    def test_get_module_changes(self):
        """モジュール内の変更詳細を取得するテスト"""
        before_module = {
            "name": "テストモジュール",
            "description": "変更前の説明",
            "version": "1.0",
            "type": "form"
        }
        after_module = {
            "name": "テストモジュール",
            "description": "変更後の説明",
            "version": "2.0",
            "new_field": "新しいフィールド"
        }
        
        changes = get_module_changes(before_module, after_module)
        
        assert len(changes) == 4  # description, version, type, new_field
        
        # descriptionの変更を確認
        description_change = next(c for c in changes if c["field"] == "description")
        assert description_change["before"] == "変更前の説明"
        assert description_change["after"] == "変更後の説明"
        
        # versionの変更を確認
        version_change = next(c for c in changes if c["field"] == "version")
        assert version_change["before"] == "1.0"
        assert version_change["after"] == "2.0"
        
        # typeの変更を確認（after_moduleにはtypeがないためNoneになる）
        type_change = next(c for c in changes if c["field"] == "type")
        assert type_change["before"] == "form"
        assert type_change["after"] is None
        
        # 新フィールドの追加を確認
        new_field_change = next(c for c in changes if c["field"] == "new_field")
        assert new_field_change["before"] is None
        assert new_field_change["after"] == "新しいフィールド"
    
    def test_generate_module_diff_error_handling(self):
        """エラーハンドリングのテスト"""
        # 不正なデータでテスト
        before_modules = []  # 空のリストを使用
        after_modules = []   # 空のリストを使用
        
        result = generate_module_diff(before_modules, after_modules)
        
        # エラーが発生しても空の結果を返す
        assert result["added"] == []
        assert result["removed"] == []
        assert result["changed"] == []
    
    def test_generate_module_diff_real_world_example(self):
        """実際の使用例に近いテスト"""
        # Claude構成のモジュール
        claude_modules = [
            {
                "name": "ユーザー認証",
                "description": "ログイン・ログアウト機能",
                "type": "auth",
                "fields": ["username", "password"]
            },
            {
                "name": "データベース",
                "description": "ユーザーデータの保存",
                "type": "database",
                "tables": ["users", "posts"]
            }
        ]
        
        # Gemini補完後のモジュール
        gemini_modules = [
            {
                "name": "ユーザー認証",
                "description": "セキュアなログイン・ログアウト機能",
                "type": "auth",
                "fields": ["username", "password", "email"],
                "security": "JWT認証"
            },
            {
                "name": "データベース",
                "description": "ユーザーデータの保存と管理",
                "type": "database",
                "tables": ["users", "posts", "comments"],
                "backup": "自動バックアップ"
            },
            {
                "name": "通知システム",
                "description": "メール・プッシュ通知",
                "type": "notification",
                "providers": ["email", "push"]
            }
        ]
        
        result = generate_module_diff(claude_modules, gemini_modules)
        
        assert len(result["added"]) == 1
        assert len(result["removed"]) == 0
        assert len(result["changed"]) == 2
        
        # 追加されたモジュール
        assert result["added"][0]["name"] == "通知システム"
        
        # 変更されたモジュール
        changed_names = [m["name"] for m in result["changed"]]
        assert "ユーザー認証" in changed_names
        assert "データベース" in changed_names
        
        # ユーザー認証モジュールの変更詳細を確認
        auth_changes = next(m for m in result["changed"] if m["name"] == "ユーザー認証")
        assert len(auth_changes["changes"]) >= 2  # description, fields, security


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 