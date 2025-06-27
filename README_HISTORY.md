# 構造履歴管理機能

## 概要

ClaudeやGeminiの構成評価・補完や、ユーザーによる保存操作の履歴を `structure_id` 単位で `data/history/{structure_id}.json` に保存する機能を実装しました。

## 実装内容

### 1. 履歴管理モジュール (`src/structure/history_manager.py`)

#### 主要機能
- `save_structure_history()`: 構造履歴を保存
- `load_structure_history()`: 構造履歴を読み込み
- `get_history_summary()`: 履歴サマリーを取得
- `cleanup_old_history()`: 古い履歴ファイルを削除

#### 保存データ構造
```json
{
  "structure_id": "abc123",
  "module_id": "senior_fitness_app",
  "timestamp": "2025-06-19T09:00:00+09:00",
  "history": [
    {
      "role": "user",
      "source": "save_structure",
      "content": "...保存内容...",
      "timestamp": "2025-06-19T08:58:00+09:00"
    },
    {
      "role": "claude",
      "source": "structure_evaluation",
      "content": "...評価結果...",
      "timestamp": "2025-06-19T09:00:00+09:00"
    }
  ]
}
```

### 2. トリガー点の実装

#### Ajax保存 (`routes/structure/base_routes.py`)
- **タイミング**: 構成をAjax保存した時
- **保存内容**: `role="user"`, `source="save_structure"`

#### Claude評価 (`src/structure/evaluator.py`)
- **タイミング**: Claude評価直後
- **保存内容**: `role="claude"`, `source="structure_evaluation"`

#### Gemini補完 (`src/structure/feedback.py`)
- **タイミング**: Gemini補完完了時
- **保存内容**: `role="gemini"`, `source="structure_completion"`

### 3. 履歴表示機能

#### ルート (`routes/structure/history_routes.py`)
- `/structure/history/<structure_id>`: 履歴表示ページ
- `/api/history/<structure_id>`: 履歴データAPI
- `/api/history/<structure_id>/summary`: 履歴サマリーAPI

#### テンプレート (`templates/structure/history.html`)
- タイムライン形式での履歴表示
- 役割別アイコン表示（user, claude, gemini）
- 内容のプレビュー/全文表示切り替え
- 履歴サマリー表示

### 4. 設定

#### .gitignore 追加
```
# History files
data/history/*.json
```

## 使用方法

### 1. 履歴の保存
```python
from src.structure.history_manager import save_structure_history

# 履歴を保存
save_structure_history(
    structure_id="your_structure_id",
    role="user",
    source="save_structure",
    content=json.dumps(your_data),
    module_id="your_module_id"
)
```

### 2. 履歴の読み込み
```python
from src.structure.history_manager import load_structure_history

# 履歴を読み込み
history_data = load_structure_history("your_structure_id")
if history_data:
    print(f"履歴エントリ数: {len(history_data['history'])}")
```

### 3. 履歴サマリーの取得
```python
from src.structure.history_manager import get_history_summary

# サマリーを取得
summary = get_history_summary("your_structure_id")
print(f"総エントリ数: {summary['total_entries']}")
print(f"役割: {summary['roles']}")
```

### 4. Web UIでの履歴表示
- 構造編集ページから履歴ページにアクセス
- URL: `/structure/history/{structure_id}`

## テスト

### 単体テスト
```bash
python test_history_simple.py
```

### テスト内容
- 新しい履歴の保存
- 既存履歴への追加
- 履歴の読み込み
- 履歴サマリーの取得
- 特殊文字の処理
- エラーハンドリング

## ログ出力

履歴保存時には以下のログが出力されます：
```
[HISTORY] Saved: structure_id (role, source)
```

## 今後の拡張予定

1. **履歴検索機能**: 日付範囲や役割での絞り込み
2. **履歴エクスポート**: CSV/JSON形式での出力
3. **履歴比較機能**: 複数バージョンの差分表示
4. **自動クリーンアップ**: 古い履歴の自動削除
5. **履歴統計**: 使用頻度や傾向の分析

## 注意事項

- 履歴ファイルは `data/history/` ディレクトリに保存されます
- ファイル名は `{structure_id}.json` 形式です
- 履歴ファイルは .gitignore で除外されているため、リポジトリには含まれません
- 大量の履歴データが蓄積される可能性があるため、定期的なクリーンアップを推奨します 