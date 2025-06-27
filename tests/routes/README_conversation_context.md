# 会話コンテキスト統合テスト

## 概要

このテストスイートは、AIDE-Xの会話コンテキスト保存・復元機能を検証する統合テストです。

## 目的

構成と評価が「浮いた状態」にならず、会話の文脈とともに理解できるUXを実現するため、以下の機能を検証します：

1. **会話コンテキストの保存**: ユーザーとAIの会話が`structure["messages"]`に正しく保存される
2. **Claude評価の文脈付き保存**: Claudeの構成・評価が`source: "claude"`で識別可能に保存される
3. **会話の時系列復元**: 保存された会話が時系列順で正しく表示される
4. **テンプレートでのsource表示**: `data-source`属性で会話の出処が視覚的に識別できる

## テスト対象

### バックエンド機能
- `send_message()`: チャット送信時の会話保存
- `autosave_structure()`: 自動保存時の会話保存
- `_evaluate_and_append_message()`: Claude評価のsource付き保存
- `unified_interface()`: 会話コンテキストの表示

### フロントエンド機能
- `getCurrentMessages()`: メッセージ取得時のsource付与
- `updateChatMessages()`: 描画時のdata-source属性付与
- `addChatMessage()`: 新規メッセージ追加時のsource設定

### テンプレート機能
- `unified_interface.html`: data-source属性の表示
- `chat_panel.html`: 会話メッセージの表示

## テストケース

### 1. 基本機能テスト
- `test_create_message_param_with_source()`: source付きメッセージ作成
- `test_message_timestamp_format()`: タイムスタンプ形式の検証

### 2. 保存機能テスト
- `test_send_message_saves_conversation_context()`: チャット送信時の保存
- `test_autosave_saves_messages_with_source()`: 自動保存時の保存

### 3. 表示機能テスト
- `test_unified_interface_displays_conversation_context()`: 会話コンテキスト表示
- `test_claude_evaluation_adds_source_claude()`: Claude評価の表示
- `test_mixed_source_types_displayed_correctly()`: 複数sourceの表示

### 4. エラーハンドリングテスト
- `test_empty_messages_handled_safely()`: 空メッセージの安全な処理

### 5. 統合テスト
- `test_conversation_flow_preserves_context()`: 会話フローでのコンテキスト保持

## 実行方法

### 個別テスト実行
```bash
# 特定のテストケースを実行
python -m pytest tests/routes/test_conversation_context.py::TestConversationContext::test_send_message_saves_conversation_context -v

# クラス全体を実行
python -m pytest tests/routes/test_conversation_context.py::TestConversationContext -v
```

### 統合テスト実行
```bash
# 専用スクリプトで実行
python tests/run_conversation_context_tests.py

# または直接pytestで実行
python -m pytest tests/routes/test_conversation_context.py -v --tb=short --color=yes
```

## 期待される結果

### 成功時の出力例
```
🧪 会話コンテキストの統合テストを開始します...
📁 作業ディレクトリ: /path/to/aide_x
🚀 実行コマンド: python -m pytest tests/routes/test_conversation_context.py -v --tb=short --color=yes --durations=10 --maxfail=5
--------------------------------------------------------------------------------
test_conversation_context.py::TestConversationContext::test_create_message_param_with_source PASSED
test_conversation_context.py::TestConversationContext::test_send_message_saves_conversation_context PASSED
test_conversation_context.py::TestConversationContext::test_autosave_saves_messages_with_source PASSED
test_conversation_context.py::TestConversationContext::test_unified_interface_displays_conversation_context PASSED
test_conversation_context.py::TestConversationContext::test_claude_evaluation_adds_source_claude PASSED
test_conversation_context.py::TestConversationContext::test_empty_messages_handled_safely PASSED
test_conversation_context.py::TestConversationContext::test_conversation_flow_preserves_context PASSED
test_conversation_context.py::TestConversationContext::test_message_timestamp_format PASSED
test_conversation_context.py::TestConversationContext::test_mixed_source_types_displayed_correctly PASSED
--------------------------------------------------------------------------------
✅ 会話コンテキストの統合テストが成功しました！

📋 テスト結果サマリー:
  - 会話コンテキストの保存機能 ✅
  - Claude評価のsource付き保存 ✅
  - テンプレートでのdata-source表示 ✅
  - 時系列順での会話表示 ✅
  - 空メッセージの安全な処理 ✅
```

## 検証ポイント

### 1. データ構造の検証
```json
{
  "messages": [
    {
      "role": "user",
      "content": "構成の目的は〇〇です",
      "timestamp": "2025-06-23T10:20:00",
      "source": "chat"
    },
    {
      "role": "assistant",
      "content": "Claude評価結果",
      "timestamp": "2025-06-23T10:20:05",
      "source": "claude",
      "type": "claude_eval"
    }
  ]
}
```

### 2. HTML出力の検証
```html
<div class="message user" data-source="chat">
  <div class="message-header">👤 あなた</div>
  <div class="message-content">構成の目的は〇〇です</div>
  <div class="message-time">2025-06-23T10:20:00</div>
</div>

<div class="message assistant" data-source="claude">
  <div class="message-header">🤖 AI</div>
  <div class="message-content">Claude評価結果</div>
  <div class="message-time">2025-06-23T10:20:05</div>
</div>
```

## トラブルシューティング

### よくある問題

1. **ImportError**: モジュールが見つからない
   ```bash
   # PYTHONPATHを設定
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **ModuleNotFoundError**: pytestが見つからない
   ```bash
   # pytestをインストール
   pip install pytest
   ```

3. **MockError**: モックが正しく動作しない
   - モック対象のパスが正しいか確認
   - 依存関係のインポート順序を確認

### デバッグ方法

1. **詳細ログ出力**
   ```bash
   python -m pytest tests/routes/test_conversation_context.py -v -s --tb=long
   ```

2. **特定テストのデバッグ**
   ```bash
   python -m pytest tests/routes/test_conversation_context.py::TestConversationContext::test_send_message_saves_conversation_context -v -s --pdb
   ```

3. **カバレッジ確認**
   ```bash
   python -m pytest tests/routes/test_conversation_context.py --cov=src.routes.unified_routes --cov-report=html
   ```

## 関連ファイル

- `src/routes/unified_routes.py`: バックエンド実装
- `static/js/unified.js`: フロントエンド実装
- `templates/structure/unified_interface.html`: テンプレート
- `tests/routes/test_conversation_context.py`: テストコード
- `tests/run_conversation_context_tests.py`: テスト実行スクリプト

## 更新履歴

- 2025-06-23: 初版作成
  - 会話コンテキスト保存・復元機能の統合テストを追加
  - source属性による会話出処の識別機能をテスト
  - 時系列順での会話表示機能をテスト 