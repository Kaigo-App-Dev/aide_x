"""
構成分析機能のテスト
"""

import pytest
from src.structure.structure_analysis import (
    analyze_structure_state,
    generate_diagnostic_message,
    get_structure_completion_rate,
    get_structure_quality_score
)


class TestStructureAnalysis:
    """構成分析機能のテストクラス"""
    
    def test_analyze_structure_state_empty(self):
        """空の構成のテスト"""
        result = analyze_structure_state({})
        
        assert result["is_empty"] is True
        assert result["module_count"] == 0
        assert result["incomplete_modules"] == []
        assert result["missing_fields"] == []
        assert result["diagnostic_message"] == "構成が空です"
    
    def test_analyze_structure_state_none(self):
        """Noneの構成のテスト"""
        result = analyze_structure_state(None)
        
        assert result["is_empty"] is True
        assert result["module_count"] == 0
        assert result["diagnostic_message"] == "構成が空です"
    
    def test_analyze_structure_state_no_modules(self):
        """モジュールが存在しない構成のテスト"""
        structure = {"title": "テスト構成", "description": "テスト説明"}
        result = analyze_structure_state(structure)
        
        assert result["is_empty"] is True
        assert result["module_count"] == 0
        assert result["diagnostic_message"] == "モジュールが定義されていません"
    
    def test_analyze_structure_state_modules_not_list(self):
        """モジュールがリストではない構成のテスト"""
        structure = {
            "title": "テスト構成",
            "modules": {"module1": {"title": "テスト"}}
        }
        result = analyze_structure_state(structure)
        
        assert result["is_empty"] is True
        assert result["module_count"] == 0
        assert result["diagnostic_message"] == "モジュールがリスト形式ではありません"
    
    def test_analyze_structure_state_empty_modules(self):
        """空のモジュールリストのテスト"""
        structure = {
            "title": "テスト構成",
            "modules": []
        }
        result = analyze_structure_state(structure)
        
        assert result["is_empty"] is True
        assert result["module_count"] == 0
        assert result["incomplete_modules"] == []
        assert result["missing_fields"] == []
        assert "モジュールが定義されていません" in result["diagnostic_message"]
    
    def test_analyze_structure_state_complete(self):
        """完成した構成のテスト"""
        structure = {
            "title": "テスト構成",
            "modules": [
                {
                    "title": "ユーザー管理",
                    "description": "ユーザーの登録・認証機能",
                    "type": "auth"
                },
                {
                    "title": "商品管理",
                    "description": "商品情報の管理機能",
                    "type": "database"
                }
            ]
        }
        result = analyze_structure_state(structure)
        
        assert result["is_empty"] is False
        assert result["module_count"] == 2
        assert result["incomplete_modules"] == []
        assert result["missing_fields"] == []
        assert "構成は完成しています" in result["diagnostic_message"]
    
    def test_analyze_structure_state_incomplete(self):
        """不完全な構成のテスト"""
        structure = {
            "title": "テスト構成",
            "modules": [
                {
                    "title": "ユーザー管理",
                    "description": "ユーザーの登録・認証機能"
                },
                {
                    "title": "商品管理"
                    # descriptionが不足
                },
                {
                    # titleが不足
                    "description": "注文処理機能"
                }
            ]
        }
        result = analyze_structure_state(structure)
        
        assert result["is_empty"] is False
        assert result["module_count"] == 3
        assert len(result["incomplete_modules"]) == 2
        
        # 不完全なモジュールの詳細チェック
        incomplete_names = [m["name"] for m in result["incomplete_modules"]]
        assert "商品管理" in incomplete_names
        assert "モジュール2" in incomplete_names  # titleがないため
        
        assert "2個のモジュールに記述漏れがあります" in result["diagnostic_message"]
    
    def test_analyze_structure_state_invalid_module(self):
        """無効なモジュール（辞書ではない）のテスト"""
        structure = {
            "title": "テスト構成",
            "modules": [
                {"title": "正常なモジュール", "description": "説明"},
                "無効なモジュール",  # 文字列
                {"title": "正常なモジュール2", "description": "説明2"}
            ]
        }
        result = analyze_structure_state(structure)
        
        assert result["is_empty"] is False
        assert result["module_count"] == 3
        assert len(result["incomplete_modules"]) == 1
        
        invalid_module = result["incomplete_modules"][0]
        assert invalid_module["index"] == 1
        assert invalid_module["name"] == "モジュール1"
        assert "辞書形式ではありません" in invalid_module["reason"]
    
    def test_analyze_structure_state_empty_fields(self):
        """空のフィールド値のテスト"""
        structure = {
            "title": "テスト構成",
            "modules": [
                {
                    "title": "",  # 空文字
                    "description": "説明"
                },
                {
                    "title": "タイトル",
                    "description": None  # None
                }
            ]
        }
        result = analyze_structure_state(structure)
        
        assert result["is_empty"] is False
        assert result["module_count"] == 2
        assert len(result["incomplete_modules"]) == 2
        
        # 空のフィールドが検出されているかチェック
        missing_fields = []
        for module in result["incomplete_modules"]:
            missing_fields.extend(module.get("missing_fields", []))
        
        assert "title" in missing_fields
        assert "description" in missing_fields
    
    def test_generate_diagnostic_message(self):
        """診断メッセージ生成のテスト"""
        # 空の場合
        empty_result = {
            "is_empty": True,
            "diagnostic_message": "構成が空です"
        }
        assert generate_diagnostic_message(empty_result) == "構成が空です"
        
        # 完成している場合
        complete_result = {
            "is_empty": False,
            "module_count": 2,
            "incomplete_modules": [],
            "missing_fields": []
        }
        message = generate_diagnostic_message(complete_result)
        assert "2個のモジュールが定義されています" in message
        assert "構成は完成しています" in message
        
        # 不完全な場合
        incomplete_result = {
            "is_empty": False,
            "module_count": 3,
            "incomplete_modules": [{"name": "モジュール1"}, {"name": "モジュール2"}],
            "missing_fields": ["description"]
        }
        message = generate_diagnostic_message(incomplete_result)
        assert "3個のモジュールが定義されています" in message
        assert "2個のモジュールに記述漏れがあります" in message
        assert "description が不足しています" in message
    
    def test_get_structure_completion_rate(self):
        """完成度計算のテスト"""
        # 空の構成
        empty_structure = {}
        assert get_structure_completion_rate(empty_structure) == 0.0
        
        # 完成した構成
        complete_structure = {
            "modules": [
                {"title": "モジュール1", "description": "説明1"},
                {"title": "モジュール2", "description": "説明2"}
            ]
        }
        assert get_structure_completion_rate(complete_structure) == 1.0
        
        # 部分的に完成した構成
        partial_structure = {
            "modules": [
                {"title": "モジュール1", "description": "説明1"},  # 完成
                {"title": "モジュール2"},  # 不完全
                {"title": "モジュール3", "description": "説明3"}   # 完成
            ]
        }
        assert get_structure_completion_rate(partial_structure) == 0.67
    
    def test_get_structure_quality_score(self):
        """品質スコア計算のテスト"""
        # 空の構成
        empty_structure = {}
        quality = get_structure_quality_score(empty_structure)
        assert quality["completion_rate"] == 0.0
        assert quality["quality_score"] == 0.0
        assert quality["total_modules"] == 0
        assert quality["complete_modules"] == 0
        
        # 完成した構成
        complete_structure = {
            "modules": [
                {"title": "モジュール1", "description": "説明1"},
                {"title": "モジュール2", "description": "説明2"}
            ]
        }
        quality = get_structure_quality_score(complete_structure)
        assert quality["completion_rate"] == 1.0
        assert quality["quality_score"] == 1.0
        assert quality["total_modules"] == 2
        assert quality["complete_modules"] == 2
        assert quality["missing_required_fields"] == 0
        
        # 不完全な構成
        incomplete_structure = {
            "modules": [
                {"title": "モジュール1", "description": "説明1"},  # 完成
                {"title": "モジュール2"},  # 不完全
                {"title": "モジュール3"}   # 不完全
            ]
        }
        quality = get_structure_quality_score(incomplete_structure)
        assert quality["completion_rate"] == 0.33
        assert quality["quality_score"] == 0.33  # 0.33 - (0 * 0.1) = 0.33 (missing_fieldsは0)
        assert quality["total_modules"] == 3
        assert quality["complete_modules"] == 1
        assert quality["missing_required_fields"] == 0  # 各モジュールにはtitleがあるため
    
    def test_real_world_example(self):
        """実際の使用例のテスト"""
        # ECサイトの構成例
        ec_structure = {
            "title": "ECサイト",
            "description": "オンラインショッピングサイト",
            "modules": [
                {
                    "title": "ユーザー管理",
                    "description": "ユーザーの登録・認証・プロフィール管理",
                    "type": "auth",
                    "dependencies": []
                },
                {
                    "title": "商品カタログ",
                    "description": "商品情報の表示・検索・カテゴリ管理",
                    "type": "database",
                    "dependencies": ["ユーザー管理"]
                },
                {
                    "title": "注文処理",
                    "description": "カート・決済・注文履歴管理",
                    "type": "business",
                    "dependencies": ["ユーザー管理", "商品カタログ"]
                },
                {
                    "title": "管理画面"
                    # descriptionが不足
                }
            ]
        }
        
        result = analyze_structure_state(ec_structure)
        
        assert result["is_empty"] is False
        assert result["module_count"] == 4
        assert len(result["incomplete_modules"]) == 1
        assert result["incomplete_modules"][0]["name"] == "管理画面"
        assert "description" in result["incomplete_modules"][0]["missing_fields"]
        
        # 完成度と品質スコア
        completion_rate = get_structure_completion_rate(ec_structure)
        quality = get_structure_quality_score(ec_structure)
        
        assert completion_rate == 0.75  # 3/4 = 0.75
        assert quality["completion_rate"] == 0.75
        assert quality["total_modules"] == 4
        assert quality["complete_modules"] == 3 