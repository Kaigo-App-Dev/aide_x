# テンプレート構成ルール（AIDE-X）

本プロジェクトでは、UIの三分割構造を以下のテンプレートに分離し、役割ごとに責任を明確にしています。

---

## 🎙️ Chat欄（ユーザー・AIの会話）

- **テンプレート**: `chat_panel.html`
- **表示領域**: `.chat-messages`
- **対応するメッセージタイプ**:
  - `user`, `assistant_reply`, `note`, `confirmation`, `revision_request`, `confirmation_accepted`

---

## 🧩 中央ペイン（Claude構成カード）

- **テンプレート**: `structure_cards.html`
- **表示領域**: `.structure-cards`
- **対応するメッセージタイプ**:
  - `structure_proposal`, `claude_structure`

---

## 🧠 右ペイン（Gemini補完構成）

- **テンプレート**: `rendered_structure.html`
- **表示領域**: `.rendered-structure`
- **出力元**: Gemini補完結果（AI構成補完）

---

## 🧷 統合画面テンプレート

- **テンプレート**: `unified_interface.html`
- **役割**: 上記テンプレートを統合表示するだけ。ロジックや描画は各テンプレートに委譲すること。
- **注意**: 統合HTML内で直接 `chat`, `structure`, `rendered` の構造をいじらない。

---

## ✅ ルールまとめ

- 各テンプレートは役割ごとに明確に分離されており、**勝手に統合・変更しないこと**
- Flask/Python側でメッセージを適切な`type`で出力し、テンプレートで描画先を振り分ける
- テストは、3ペインが意図通り分離表示されることを前提とする

## ✅ AIDE-X 会話・構成生成の一連の流れ（自動化設計）

AIDE-Xでは、ユーザーの入力に対して ChatGPTが構成を即座に提案し、Claudeで評価し、Geminiで補完する一連の自動フローを採用している。

### 🎯 自動構成生成・評価・補完の流れ
1. ユーザーが自由に入力
2. ChatGPTが即座に `title`, `content` を持つ構成JSONを出力（type: assistant_reply）
3. Claudeで構成を評価し、中央に `structure_proposal` を表示
4. Geminiで構成を補完し、右ペインに `gemini_ui` を表示

### ❌ 確認プロンプトや仮応答は廃止
- ChatGPTが確認だけ返すパターン（type: confirmation）は廃止
- 構成生成は必須（抽出できない場合は再プロンプト）
- 失敗時は明示的なエラー案内を行い、会話が途切れないようにする

### ✅ UXとしてのメリット
- 入力1回で構成カード（中央）と補完（右）が必ず表示される
- 「仮応答で止まる」「中央が空白」といったUX欠陥を回避

- Chatセクションに表示される条件は `type in ["user", "assistant", "assistant_reply"]`
- Claudeによる構成カードは `type == "structure_proposal"`
- `messages` は常に `index` 昇順で描画される必要あり
- ChatGPTの応答が構成JSONでない場合も自然文は `assistant_reply` として必ず表示
