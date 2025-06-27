# E2E (End-to-End) テスト

このディレクトリには、統合UIのE2Eテストが含まれています。

## 概要

E2Eテストは、ChatGPT → Claude → ユーザー確認 → Gemini の構成生成フローが
UI上で意図通りに動作するかを自動で検証します。

## テスト内容

### test_structure_flow.py

構成確認フローのE2Eテスト：

1. ユーザーが初回の入力を送信
2. ChatGPTの構成提案が表示される
3. Claude評価が表示される
4. ChatGPTが「この構成でよろしいですか？」と確認
5. ユーザーが「いいえ」と答える
6. ChatGPTが不満点を聞いてくる

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r tests/e2e/requirements.txt
```

### 2. Playwrightブラウザのインストール

```bash
playwright install chromium
```

### 3. アプリケーションの起動

```bash
python src/app.py
```

## 実行方法

### 基本的な実行

```bash
python tests/e2e/test_structure_flow.py
```

### pytestを使用した実行

```bash
pytest tests/e2e/test_structure_flow.py -v
```

### 特定のテストのみ実行

```bash
pytest tests/e2e/test_structure_flow.py::test_structure_confirmation_flow -v
```

## テスト結果

- 成功時: `structure_flow_test_result.png` が生成されます
- 失敗時: `structure_flow_test_error.png` が生成されます

## 注意事項

- テスト実行前に `http://localhost:5000` でアプリケーションが起動している必要があります
- テストは非ヘッドレスモードで実行されるため、ブラウザの動作を確認できます
- AI応答の待機時間が含まれているため、テスト実行には時間がかかります

## トラブルシューティング

### Playwrightのインストールエラー

```bash
# システムの依存関係を確認
playwright install-deps
```

### ブラウザが見つからない

```bash
# ブラウザを再インストール
playwright install chromium
```

### テストが失敗する場合

1. アプリケーションが正常に起動しているか確認
2. ネットワーク接続を確認
3. ログを確認してエラーの詳細を把握
4. スクリーンショットを確認してUIの状態を把握 