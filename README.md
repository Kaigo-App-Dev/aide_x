# AI Evaluation System

## テスト実行

以下のコマンドでテストを実行できます：

```bash
# Windows (PowerShell)
$env:PYTHONPATH = "."; pytest tests/ -v

# Linux/macOS
PYTHONPATH=. pytest tests/ -v
```

## 環境変数

テスト実行時に以下の環境変数が必要です：

- `ANTHROPIC_API_KEY`: Claude APIのキー
- `GEMINI_API_KEY`: Gemini APIのキー

## プロジェクト構成

```
src/
  ├── common/
  │   ├── exceptions.py  # 例外定義
  │   ├── logger.py      # ログ保存
  │   └── types.py       # 共通型定義
  ├── llm/
  │   ├── providers/     # AIプロバイダ実装
  │   ├── prompts/       # プロンプト定義
  │   └── hub.py         # AI呼び出しハブ
  └── structure/
      └── evaluator.py   # 構造評価

tests/
  ├── conftest.py        # テスト共通設定
  └── test_evaluator.py  # 評価テスト
```

## ログ

ログは `logs/` ディレクトリに保存されます：

- `logs/general/`: 一般的なログ
- `logs/error/`: エラーログ
- `logs/evaluation/`: 評価ログ 