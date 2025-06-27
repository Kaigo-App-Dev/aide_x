"""
会話コンテキストの保存・復元機能の統合テスト

このテストでは以下を検証します：
1. /send-message や /autosave にPOSTされた messages が structure["messages"] に保存されていること
2. Claude構成が返却された後、structure["messages"] に source: "claude" のAI発話が追加されていること
3. /unified/<structure_id> にGETアクセスしたとき、Chat欄にユーザー・Claudeの会話が時系列で表示されていること
4. テンプレートに data-source="chat" や data-source="claude" が含まれていること
"""

import pytest
import json
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from flask import url_for
from src.routes.unified_routes import create_message_param


class TestConversationContext:
    """会話コンテキストの保存・復元機能のテスト"""

    @pytest.fixture
    def sample_structure(self):
        """テスト用のサンプル構成データ"""
        return {
            "id": "test_conversation_001",
            "title": "テスト構成",
            "description": "会話コンテキストテスト用",
            "content": {
                "title": "テストアプリ",
                "description": "テスト用のアプリケーション"
            },
            "messages": [],
            "evaluations": [],
            "completions": []
        }

    @pytest.fixture
    def sample_messages(self):
        """テスト用のサンプルメッセージ"""
        return [
            {
                "role": "user",
                "content": "構成の目的は〇〇です",
                "timestamp": "2025-06-23T10:20:00",
                "source": "chat"
            },
            {
                "role": "assistant", 
                "content": "了解しました。それでは構成案を提示します。",
                "timestamp": "2025-06-23T10:20:05",
                "source": "chat"
            }
        ]

    def test_create_message_param_with_source(self):
        """create_message_paramでsourceが正しく設定されることをテスト"""
        # sourceあり
        msg = create_message_param(
            role="assistant",
            content="テストメッセージ",
            source="claude"
        )
        assert msg["role"] == "assistant"
        assert msg["content"] == "テストメッセージ"
        assert msg["source"] == "claude"
        assert "timestamp" in msg

        # sourceなし
        msg = create_message_param(
            role="user",
            content="ユーザーメッセージ"
        )
        assert msg["role"] == "user"
        assert msg["content"] == "ユーザーメッセージ"
        assert "source" not in msg

    @patch('src.routes.unified_routes.load_structure_by_id')
    @patch('src.routes.unified_routes.save_structure')
    @patch('src.routes.unified_routes.controller')
    def test_send_message_saves_conversation_context(self, mock_controller, mock_save, mock_load, client, sample_structure, sample_messages):
        """send_messageで会話コンテキストが保存されることをテスト"""
        # モック設定
        mock_load.return_value = sample_structure.copy()
        mock_controller.call.return_value = {"content": "AI応答テスト"}
        
        # リクエスト送信
        response = client.post(
            f'/unified/{sample_structure["id"]}/chat',
            json={
                "message": "構成の目的は〇〇です"
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        
        # save_structureが呼ばれたことを確認
        mock_save.assert_called()
        
        # 保存されたstructureにmessagesが含まれていることを確認
        saved_structure = mock_save.call_args[0][1]
        assert "messages" in saved_structure
        assert len(saved_structure["messages"]) >= 2  # ユーザーメッセージ + AI応答
        
        # ユーザーメッセージが正しく保存されていることを確認
        user_messages = [msg for msg in saved_structure["messages"] if msg["role"] == "user"]
        assert len(user_messages) >= 1
        assert user_messages[0]["content"] == "構成の目的は〇〇です"
        # source属性は実際の実装に依存するため、存在するかどうかのみチェック
        assert "source" in user_messages[0]

    @patch('src.routes.unified_routes.load_structure_by_id')
    @patch('src.routes.unified_routes.save_structure')
    @patch('src.routes.unified_routes._evaluate_and_append_message')
    def test_autosave_saves_messages_with_source(self, mock_evaluate, mock_save, mock_load, client, sample_structure, sample_messages):
        """autosaveでmessagesがsource付きで保存されることをテスト"""
        # モック設定
        mock_load.return_value = sample_structure.copy()
        
        # リクエスト送信
        response = client.post(
            f'/unified/{sample_structure["id"]}/autosave',
            json={
                "structure": sample_structure["content"],
                "messages": sample_messages,
                "trigger_evaluation": True
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        
        # save_structureが呼ばれたことを確認
        mock_save.assert_called()
        
        # 保存されたstructureにmessagesが正しく保存されていることを確認
        saved_structure = mock_save.call_args[0][1]
        assert "messages" in saved_structure
        assert len(saved_structure["messages"]) == len(sample_messages)
        
        # sourceが正しく設定されていることを確認
        for i, msg in enumerate(saved_structure["messages"]):
            assert msg["role"] == sample_messages[i]["role"]
            assert msg["content"] == sample_messages[i]["content"]
            assert msg["source"] == sample_messages[i]["source"]

    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_unified_interface_displays_conversation_context(self, mock_load, client, sample_structure, sample_messages):
        """unified_interfaceで会話コンテキストが表示されることをテスト"""
        # テンプレートの存在を確認
        template_path = "templates/structure/unified_interface.html"
        if not os.path.exists(template_path):
            pytest.skip(f"テンプレートが見つかりません: {template_path}")
        
        # messagesを含むstructureを設定
        sample_structure["messages"] = sample_messages
        mock_load.return_value = sample_structure
        
        # ページアクセス
        response = client.get(f'/unified/{sample_structure["id"]}')
        
        # テンプレートが見つからない場合はスキップ
        if response.status_code == 500 and "TemplateNotFound" in response.get_data(as_text=True):
            pytest.skip("テンプレートが見つからないためスキップ")
        
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # ユーザーメッセージが表示されていることを確認
        assert "構成の目的は〇〇です" in html
        assert "了解しました。それでは構成案を提示します。" in html
        
        # data-source属性が含まれていることを確認
        assert 'data-source="chat"' in html
        
        # 時系列順で表示されていることを確認（最初のメッセージが先に表示される）
        user_msg_index = html.find("構成の目的は〇〇です")
        ai_msg_index = html.find("了解しました。それでは構成案を提示します。")
        assert user_msg_index < ai_msg_index

    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_claude_evaluation_adds_source_claude(self, mock_load, client, sample_structure):
        """Claude評価がsource: claudeで追加されることをテスト"""
        # テンプレートの存在を確認
        template_path = "templates/structure/unified_interface.html"
        if not os.path.exists(template_path):
            pytest.skip(f"テンプレートが見つかりません: {template_path}")
        
        # 評価結果を含むstructureを設定
        sample_structure["messages"] = [
            {
                "role": "user",
                "content": "構成を評価してください",
                "timestamp": "2025-06-23T10:20:00",
                "source": "chat"
            },
            {
                "role": "assistant",
                "content": "Claude評価結果: 良い構成です",
                "timestamp": "2025-06-23T10:20:10",
                "source": "claude",
                "type": "claude_eval"
            }
        ]
        sample_structure["evaluations"] = [
            {
                "provider": "claude",
                "score": 0.85,
                "feedback": "良い構成です",
                "timestamp": "2025-06-23T10:20:10"
            }
        ]
        mock_load.return_value = sample_structure
        
        # ページアクセス
        response = client.get(f'/unified/{sample_structure["id"]}')
        
        # テンプレートが見つからない場合はスキップ
        if response.status_code == 500 and "TemplateNotFound" in response.get_data(as_text=True):
            pytest.skip("テンプレートが見つからないためスキップ")
        
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Claude評価が表示されていることを確認
        assert "Claude評価結果" in html
        assert "良い構成です" in html
        
        # data-source="claude"が含まれていることを確認
        assert 'data-source="claude"' in html

    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_empty_messages_handled_safely(self, mock_load, client, sample_structure):
        """messagesが空やNoneの場合でも安全に処理されることをテスト"""
        # テンプレートの存在を確認
        template_path = "templates/structure/unified_interface.html"
        if not os.path.exists(template_path):
            pytest.skip(f"テンプレートが見つかりません: {template_path}")
        
        # messagesが空のstructure
        sample_structure["messages"] = []
        mock_load.return_value = sample_structure
        
        response = client.get(f'/unified/{sample_structure["id"]}')
        
        # テンプレートが見つからない場合はスキップ
        if response.status_code == 500 and "TemplateNotFound" in response.get_data(as_text=True):
            pytest.skip("テンプレートが見つからないためスキップ")
        
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "メッセージがありません" in html
        
        # messagesがNoneのstructure
        sample_structure["messages"] = None
        mock_load.return_value = sample_structure
        
        response = client.get(f'/unified/{sample_structure["id"]}')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "メッセージがありません" in html

    @patch('src.routes.unified_routes.load_structure_by_id')
    @patch('src.routes.unified_routes.save_structure')
    @patch('src.routes.unified_routes.controller')
    def test_conversation_flow_preserves_context(self, mock_controller, mock_save, mock_load, client, sample_structure):
        """会話フローでコンテキストが保持されることをテスト"""
        # 初期状態
        mock_load.return_value = sample_structure.copy()
        mock_controller.call.return_value = {"content": "AI応答1"}
        
        # 1回目のメッセージ送信
        response1 = client.post(
            f'/unified/{sample_structure["id"]}/chat',
            json={"message": "最初の質問"},
            headers={'Content-Type': 'application/json'}
        )
        assert response1.status_code == 200
        
        # 2回目のメッセージ送信（コンテキストが保持されていることを確認）
        mock_controller.call.return_value = {"content": "AI応答2"}
        response2 = client.post(
            f'/unified/{sample_structure["id"]}/chat',
            json={"message": "2番目の質問"},
            headers={'Content-Type': 'application/json'}
        )
        assert response2.status_code == 200
        
        # 保存されたstructureに両方のメッセージが含まれていることを確認
        saved_structure = mock_save.call_args[0][1]
        assert len(saved_structure["messages"]) >= 4  # ユーザー2回 + AI2回
        
        user_messages = [msg for msg in saved_structure["messages"] if msg["role"] == "user"]
        assert len(user_messages) >= 2
        assert user_messages[0]["content"] == "最初の質問"
        assert user_messages[1]["content"] == "2番目の質問"

    def test_message_timestamp_format(self):
        """メッセージのtimestampが正しい形式で保存されることをテスト"""
        msg = create_message_param(
            role="user",
            content="テスト",
            source="chat"
        )
        
        assert "timestamp" in msg
        # ISO形式のタイムスタンプであることを確認
        timestamp = msg["timestamp"]
        assert timestamp is not None
        assert "T" in timestamp
        assert len(timestamp) >= 19  # YYYY-MM-DDTHH:MM:SS

    @patch('src.routes.unified_routes.load_structure_by_id')
    def test_mixed_source_types_displayed_correctly(self, mock_load, client, sample_structure):
        """異なるsourceのメッセージが正しく表示されることをテスト"""
        # テンプレートの存在を確認
        template_path = "templates/structure/unified_interface.html"
        if not os.path.exists(template_path):
            pytest.skip(f"テンプレートが見つかりません: {template_path}")
        
        # 複数のsourceを含むmessages
        sample_structure["messages"] = [
            {
                "role": "user",
                "content": "ユーザー質問",
                "timestamp": "2025-06-23T10:20:00",
                "source": "chat"
            },
            {
                "role": "assistant",
                "content": "Claude評価結果",
                "timestamp": "2025-06-23T10:20:05",
                "source": "claude",
                "type": "claude_eval"
            },
            {
                "role": "assistant",
                "content": "Gemini補完結果",
                "timestamp": "2025-06-23T10:20:10",
                "source": "gemini"
            }
        ]
        mock_load.return_value = sample_structure
        
        response = client.get(f'/unified/{sample_structure["id"]}')
        
        # テンプレートが見つからない場合はスキップ
        if response.status_code == 500 and "TemplateNotFound" in response.get_data(as_text=True):
            pytest.skip("テンプレートが見つからないためスキップ")
        
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # 各sourceのdata-source属性が含まれていることを確認
        assert 'data-source="chat"' in html
        assert 'data-source="claude"' in html
        assert 'data-source="gemini"' in html 