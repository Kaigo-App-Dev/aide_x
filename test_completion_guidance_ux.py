#!/usr/bin/env python3
"""
自然な会話から構成を育てるUX機能のテスト
"""

import json
import pytest
from unittest.mock import Mock, patch
from src.routes.unified_routes import (
    prepare_prompt_for_structure,
    check_structure_completeness,
    render_completion_check_message,
    render_guidance_message,
    auto_complete_structure
)

class TestCompletionGuidanceUX:
    """構成補完UX機能のテストクラス"""
    
    def test_prepare_prompt_for_structure(self):
        """プロンプト補完機能のテスト"""
        user_input = "タスク管理アプリを作りたい"
        
        prompt = prepare_prompt_for_structure(user_input)
        
        # 基本的な要素が含まれているかチェック
        assert "ユーザーの入力" in prompt
        assert user_input in prompt
        assert "JSON形式" in prompt
        assert "title" in prompt
        assert "content" in prompt
        assert "対象ユーザー" in prompt
        assert "主要機能" in prompt
        assert "技術要件" in prompt
        assert "画面構成" in prompt
        assert "自然文禁止" in prompt
        
        print("✅ プロンプト補完機能テスト完了")
    
    def test_check_structure_completeness_complete(self):
        """完全な構成のチェックテスト"""
        complete_structure = {
            "title": "タスク管理アプリ",
            "description": "個人向けタスク管理アプリケーション",
            "content": {
                "対象ユーザー": "個人ユーザー",
                "主要機能": {
                    "タスク作成": "新しいタスクを作成",
                    "タスク管理": "タスクの編集・削除"
                },
                "技術要件": {
                    "フロントエンド": "React",
                    "バックエンド": "Node.js",
                    "データベース": "MongoDB"
                },
                "画面構成": {
                    "ダッシュボード": "タスク一覧表示",
                    "タスク作成": "新規タスク作成画面"
                }
            }
        }
        
        result = check_structure_completeness(complete_structure)
        
        assert result["is_complete"] == True
        assert len(result["missing_fields"]) == 0
        assert len(result["suggestions"]) == 0
        
        print("✅ 完全な構成チェックテスト完了")
    
    def test_check_structure_completeness_incomplete(self):
        """不完全な構成のチェックテスト"""
        incomplete_structure = {
            "title": "タスク管理アプリ",
            "content": {
                "主要機能": {
                    "タスク作成": "新しいタスクを作成"
                }
            }
        }
        
        result = check_structure_completeness(incomplete_structure)
        
        assert result["is_complete"] == False
        assert "構成の説明" in result["missing_fields"]
        assert "対象ユーザー" in result["missing_fields"]
        assert "技術要件" in result["missing_fields"]
        assert "画面構成" in result["missing_fields"]
        assert "主要機能" not in result["missing_fields"]
        assert len(result["suggestions"]) > 0
        
        print("✅ 不完全な構成チェックテスト完了")
    
    def test_render_completion_check_message(self):
        """補完確認メッセージ生成テスト"""
        missing_fields = ["対象ユーザー", "技術要件"]
        suggestions = ["誰が使うアプリか教えてください", "使用したい技術があれば教えてください"]
        
        message = render_completion_check_message(missing_fields, suggestions)
        
        assert "⚠️ この構成には不足があります" in message
        assert "対象ユーザー" in message
        assert "技術要件" in message
        assert "誰が使うアプリか教えてください" in message
        assert "自動補完してもよろしいですか" in message
        assert "はい" in message
        assert "いいえ" in message
        assert "completion-confirmation" in message
        
        print("✅ 補完確認メッセージ生成テスト完了")
    
    def test_render_guidance_message(self):
        """ガイダンスメッセージ生成テスト"""
        missing_fields = ["対象ユーザー", "画面構成"]
        suggestions = ["誰が使うアプリか教えてください", "どんな画面が必要か教えてください"]
        
        message = render_guidance_message(missing_fields, suggestions)
        
        assert "👍 OK！一緒に考えていきましょう" in message
        assert "対象ユーザー" in message
        assert "画面構成" in message
        assert "誰が使うアプリか教えてください" in message
        assert "どんな画面が必要か教えてください" in message
        assert "補完のために、教えてください" in message
        assert "💡 ヒント" in message
        
        print("✅ ガイダンスメッセージ生成テスト完了")
    
    @patch('src.routes.unified_routes.controller')
    def test_auto_complete_structure_success(self, mock_controller):
        """自動補完機能の成功テスト"""
        # モックの設定
        mock_response = {
            'content': '''```json
{
  "title": "改善されたタスク管理アプリ",
  "description": "個人向けの使いやすいタスク管理アプリケーション",
  "content": {
    "対象ユーザー": "個人ユーザー、学生、ビジネスパーソン",
    "主要機能": {
      "タスク作成": "簡単なタスク作成機能",
      "タスク管理": "タスクの編集・削除・完了管理"
    },
    "技術要件": {
      "フロントエンド": "React + TypeScript",
      "バックエンド": "Node.js + Express",
      "データベース": "MongoDB"
    },
    "画面構成": {
      "ダッシュボード": "タスク一覧と進捗表示",
      "タスク作成": "新規タスク作成フォーム",
      "タスク詳細": "タスクの詳細表示・編集"
    }
  }
}
```'''
        }
        mock_controller.call.return_value = mock_response
        
        # テスト用の不完全な構成
        incomplete_structure = {
            "title": "タスク管理アプリ",
            "content": {
                "主要機能": {
                    "タスク作成": "新しいタスクを作成"
                }
            }
        }
        
        missing_fields = ["対象ユーザー", "技術要件", "画面構成"]
        
        # 自動補完を実行
        result = auto_complete_structure(incomplete_structure, missing_fields)
        
        # 結果の検証
        assert result["title"] == "改善されたタスク管理アプリ"
        assert result["description"] == "個人向けの使いやすいタスク管理アプリケーション"
        assert "対象ユーザー" in result["content"]
        assert "技術要件" in result["content"]
        assert "画面構成" in result["content"]
        
        # contentにtitleやdescriptionが含まれないことを確認
        assert "title" not in result["content"]
        assert "description" not in result["content"]
        
        # モックが正しく呼ばれたかチェック
        mock_controller.call.assert_called_once()
        
        print("✅ 自動補完機能成功テスト完了")
    
    @patch('src.routes.unified_routes.controller')
    def test_auto_complete_structure_failure(self, mock_controller):
        """自動補完機能の失敗テスト"""
        # モックの設定（空の応答）
        mock_controller.call.return_value = {'content': ''}
        
        # テスト用の不完全な構成
        incomplete_structure = {
            "title": "タスク管理アプリ",
            "content": {
                "主要機能": {
                    "タスク作成": "新しいタスクを作成"
                }
            }
        }
        
        missing_fields = ["対象ユーザー"]
        
        # 自動補完を実行
        result = auto_complete_structure(incomplete_structure, missing_fields)
        
        # 元の構成が変更されていないことを確認
        assert result["title"] == "タスク管理アプリ"
        assert "対象ユーザー" not in result["content"]
        
        print("✅ 自動補完機能失敗テスト完了")

def run_tests():
    """テストを実行"""
    print("🧪 自然な会話から構成を育てるUX機能のテスト開始")
    print("=" * 60)
    
    test_instance = TestCompletionGuidanceUX()
    
    # 各テストを実行
    test_instance.test_prepare_prompt_for_structure()
    test_instance.test_check_structure_completeness_complete()
    test_instance.test_check_structure_completeness_incomplete()
    test_instance.test_render_completion_check_message()
    test_instance.test_render_guidance_message()
    test_instance.test_auto_complete_structure_success()
    test_instance.test_auto_complete_structure_failure()
    
    print("=" * 60)
    print("🎉 すべてのテストが完了しました！")

if __name__ == "__main__":
    run_tests() 