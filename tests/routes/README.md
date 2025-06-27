# 統合インターフェーステスト

このディレクトリには、`/unified/<structure_id>` エンドポイントの統合テストが含まれています。

## テストの目的

- 評価履歴が空でも `/unified/<structure_id>` が500にならず200で返ることを確認
- Claude評価が1件ある場合、`latest_evaluation` が正しく表示されることを確認
- Gemini補完構成がない場合、改善構成カードが非表示または案内文になることを確認
- 評価結果がHTMLに出力されていることを確認（強み・弱み・提案）

## テストケース

### 1. 評価履歴が空の場合 (`test_unified_interface_empty_evaluations`)
- **目的**: 評価履歴が空の構成にアクセスしてもエラーが発生しないことを確認
- **期待結果**: 
  - ステータスコード: 200
  - "まだ評価が実行されていません" メッセージが表示
  - Jinja2エラーが発生しない

### 2. Claude評価済みの場合 (`test_unified_interface_with_evaluation`)
- **目的**: 評価済みの構成で最新評価が正しく表示されることを確認
- **期待結果**:
  - スコア85%が表示
  - 評価フィードバックが表示
  - 強み・弱み・改善提案が表示
  - 意図一致90%、明確性80%が表示

### 3. 改善構成ありの場合 (`test_unified_interface_with_improved_structure`)
- **目的**: 改善構成が生成された場合の表示を確認
- **期待結果**:
  - "改善構成提案" カードが表示
  - "Gemini生成" バッジが表示
  - 改善理由（Claude提案）が表示
  - 評価・採用・差分表示ボタンが表示

### 4. 改善構成なしの場合 (`test_unified_interface_without_improved_structure`)
- **目的**: 改善構成がない場合の表示を確認
- **期待結果**:
  - 改善構成カードが表示されない
  - 評価結果は正常に表示される

### 5. HTML構造の検証 (`test_unified_interface_evaluation_html_structure`)
- **目的**: 評価結果のHTML構造が正しいことを確認
- **期待結果**:
  - 評価カードのHTML構造が正しい
  - スコア表示の構造が正しい
  - 改善提案のリスト構造が正しい

### 6. 空の構成データ (`test_unified_interface_empty_structure_handling`)
- **目的**: 完全に空の構成データの処理を確認
- **期待結果**:
  - "構成データがありません" メッセージが表示
  - エラーが発生しない

### 7. 不正な評価データ (`test_unified_interface_malformed_evaluation_data`)
- **目的**: 不完全な評価データの処理を確認
- **期待結果**:
  - エラーが発生しない
  - 基本的なUIが表示される

## テストの実行方法

### 全テストの実行
```bash
# プロジェクトルートディレクトリで実行
python tests/run_unified_interface_tests.py
```

### 特定のテストの実行
```bash
# 特定のテストメソッドを実行
python tests/run_unified_interface_tests.py TestUnifiedInterface::test_unified_interface_empty_evaluations
```

### pytest直接実行
```bash
# 詳細出力で実行
pytest tests/routes/test_unified_interface.py -v

# カバレッジ付きで実行
pytest tests/routes/test_unified_interface.py --cov=src/routes/unified_routes --cov-report=html
```

## CI/CD統合

このテストは以下のGitHub Actionsワークフローで自動実行されます：

- **ファイル変更時**: `templates/structure/unified_interface.html`, `static/css/unified.css`, `static/js/unified.js`, `src/routes/unified_routes.py` が変更された場合
- **Python バージョン**: 3.9, 3.10, 3.11
- **追加チェック**: セキュリティスキャン、テンプレート検証

## テストデータ

テストでは以下のフィクスチャを使用します：

- `empty_structure_data`: 評価履歴が空の構成
- `evaluated_structure_data`: Claude評価済みの構成
- `improved_structure_data`: 改善構成ありの構成

## トラブルシューティング

### よくある問題

1. **ImportError**: 依存関係が不足している場合
   ```bash
   pip install -r requirements.txt
   ```

2. **TemplateNotFound**: テンプレートファイルが見つからない場合
   - プロジェクトルートディレクトリで実行していることを確認
   - テンプレートファイルのパスが正しいことを確認

3. **Mock設定エラー**: モックが正しく設定されていない場合
   - `@patch` デコレータのパスが正しいことを確認
   - モックの戻り値が適切に設定されていることを確認

### デバッグ方法

```bash
# デバッグ出力付きで実行
pytest tests/routes/test_unified_interface.py -v -s --tb=long

# 特定のテストをデバッグ
pytest tests/routes/test_unified_interface.py::TestUnifiedInterface::test_unified_interface_empty_evaluations -v -s
```

## テストの拡張

新しいテストケースを追加する場合：

1. `TestUnifiedInterface` クラスに新しいテストメソッドを追加
2. 必要に応じて新しいフィクスチャを作成
3. テストの期待結果を明確に記述
4. CI/CDワークフローでテストが実行されることを確認

## 関連ファイル

- `tests/routes/test_unified_interface.py`: メインテストファイル
- `tests/run_unified_interface_tests.py`: テスト実行スクリプト
- `.github/workflows/unified-interface-tests.yml`: CI/CDワークフロー
- `templates/structure/unified_interface.html`: テスト対象テンプレート
- `templates/components/improved_structure_card.html`: 改善構成カードテンプレート 