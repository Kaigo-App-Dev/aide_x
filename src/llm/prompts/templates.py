"""
プロンプトテンプレート管理モジュール
"""

from typing import Dict, Any
from .manager import PromptManager, Prompt, prompt_manager

def register_all_templates(prompt_manager: PromptManager) -> None:
    """すべてのプロンプトテンプレートを登録する"""
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔄 register_all_templates 開始")
    
    try:
        # ChatGPT用テンプレート
        chatgpt_templates = {
            "chat": """あなたは親切で丁寧なAIアシスタントです。
ユーザーの質問や要望に対して、分かりやすく回答してください。
必要に応じて、具体的な例や説明を加えてください。

ユーザーの入力: {user_input}""",
            "evaluation": """以下の構造を評価し、スコアとフィードバックを提供してください。

構造:
{user_input}

評価基準:
1. 意図との一致度
2. 構造の明確さ
3. 実装の容易さ

評価結果は以下のJSON形式で返してください:
{{
  "score": 0-100の数値,
  "feedback": "評価の詳細な説明",
  "details": {{
    "intent_match": "意図との一致度に関する詳細",
    "clarity": "構造の明確さに関する詳細",
    "implementation": "実装の容易さに関する詳細"
  }}
}}""",
            "structure_generation": """あなたはプロダクト構成アシスタントです。ユーザーの要求に基づいて、必ずJSON形式で構成を出力してください。

要求内容：{{ user_input }}

**重要**: 以下の厳密な形式で必ずJSON形式で構成を出力してください。自然文での説明、リスト形式、その他の形式は一切含めないでください。

```json
{{
  "title": "構成タイトル",
  "description": "構成の説明（任意）",
  "modules": [
    {{
      "id": "module-001",
      "type": "form",
      "title": "ユーザー登録フォーム",
      "description": "利用者の基本情報を入力する画面",
      "fields": [
        {{"label": "名前", "name": "name", "type": "text", "required": true}},
        {{"label": "メールアドレス", "name": "email", "type": "email", "required": true}},
        {{"label": "生年月日", "name": "birthdate", "type": "date", "required": false}}
      ]
    }},
    {{
      "id": "module-002", 
      "type": "table",
      "title": "ユーザー一覧",
      "description": "登録済みユーザーの一覧表示",
      "columns": [
        {{"key": "id", "label": "ID", "type": "text"}},
        {{"key": "name", "label": "名前", "type": "text"}},
        {{"key": "email", "label": "メール", "type": "text"}},
        {{"key": "actions", "label": "操作", "type": "actions"}}
      ]
    }}
  ]
}}
```

**必須項目**:
- `title`: 構成のタイトル（必須）
- `modules`: モジュール配列（必須、最低1個以上）
- 各モジュールの `id`: ユニークなID（必須）
- 各モジュールの `type`: モジュールタイプ（必須）
- 各モジュールの `title`: モジュールタイトル（必須）
- 各モジュールの `fields` または `columns`: フィールド/カラム定義（必須）

**モジュールタイプ（type）の指定**:
- `form`: 入力フォーム（fields配列が必要）
- `table`: データテーブル（columns配列が必要）
- `api`: APIエンドポイント（endpoints配列が必要）
- `chart`: グラフ・チャート（chart_configが必要）
- `auth`: 認証機能（auth_configが必要）
- `database`: データベース（tables配列が必要）
- `config`: 設定画面（settings配列が必要）
- `page`: ページ・ビュー（layoutが必要）
- `component`: コンポーネント（component_configが必要）

**フィールド定義（fields）の例**:
```json
"fields": [
  {{"label": "フィールド名", "name": "field_name", "type": "text", "required": true}},
  {{"label": "選択肢", "name": "options", "type": "select", "options": ["選択肢1", "選択肢2"]}},
  {{"label": "チェックボックス", "name": "checkbox", "type": "checkbox", "default": false}}
]
```

**カラム定義（columns）の例**:
```json
"columns": [
  {{"key": "id", "label": "ID", "type": "text"}},
  {{"key": "name", "label": "名前", "type": "text"}},
  {{"key": "status", "label": "ステータス", "type": "badge"}},
  {{"key": "actions", "label": "操作", "type": "actions"}}
]
```

**出力ルール**:
1. 必ずJSON形式のみで出力
2. 自然文での説明は一切含めない
3. リスト形式や箇条書きは使用しない
4. コードブロック（```json）で囲む
5. titleとmodulesは必須フィールド
6. descriptionは任意フィールド
7. 各モジュールにid、type、titleは必須
8. モジュールタイプに応じてfields、columns、endpointsなどを含める

**禁止事項**:
- 自然文での説明
- リスト形式での出力
- 箇条書きでの出力
- JSON以外の形式
- コードブロック外での説明
- 不完全なモジュール定義（id、type、titleの欠落）

**具体例**:
ユーザーが「ブログサイトの構成を作成してください」と言った場合：

```json
{{
  "title": "ブログサイト構成",
  "description": "個人ブログサイトの基本構成",
  "modules": [
    {{
      "id": "header-001",
      "type": "component",
      "title": "ヘッダー",
      "description": "サイトのヘッダー部分",
      "component_config": {{
        "logo": "サイトロゴ",
        "navigation": ["ホーム", "記事", "カテゴリ", "お問い合わせ"],
        "search": true
      }}
    }},
    {{
      "id": "article-list-001",
      "type": "table",
      "title": "記事一覧",
      "description": "最新記事の表示",
      "columns": [
        {{"key": "title", "label": "タイトル", "type": "text"}},
        {{"key": "author", "label": "著者", "type": "text"}},
        {{"key": "date", "label": "投稿日", "type": "date"}},
        {{"key": "category", "label": "カテゴリ", "type": "badge"}},
        {{"key": "actions", "label": "操作", "type": "actions"}}
      ]
    }},
    {{
      "id": "article-form-001",
      "type": "form",
      "title": "記事投稿フォーム",
      "description": "新しい記事を投稿するフォーム",
      "fields": [
        {{"label": "タイトル", "name": "title", "type": "text", "required": true}},
        {{"label": "カテゴリ", "name": "category", "type": "select", "options": ["技術", "生活", "趣味"], "required": true}},
        {{"label": "本文", "name": "content", "type": "textarea", "required": true}},
        {{"label": "公開設定", "name": "published", "type": "checkbox", "default": false}}
      ]
    }},
    {{
      "id": "sidebar-001",
      "type": "component",
      "title": "サイドバー",
      "description": "サイトのサイドバー部分",
      "component_config": {{
        "profile": "著者情報",
        "categories": "カテゴリメニュー",
        "recent_posts": "最新記事リスト"
      }}
    }}
  ]
}}
```

**最終確認**:
- 出力は必ずJSON形式のみ
- 自然文やMarkdownは一切含めない
- コードブロック（```json）で囲む
- 有効なJSON構文であることを確認
- 各モジュールにid、type、titleが含まれていることを確認
- モジュールタイプに応じた適切な配列（fields、columns等）が含まれていることを確認

必ず上記の厳密なJSON形式で出力してください。"""
        }
        
        chatgpt_descriptions = {
            "chat": "ChatGPT用の基本的なチャット応答プロンプト",
            "evaluation": "ChatGPT用の構造評価プロンプト",
            "structure_generation": "ChatGPT用の構成生成プロンプト"
        }
        
        # Claude用テンプレート
        claude_templates = {
            "chat": """あなたは親切で丁寧なAIアシスタントです。
ユーザーの質問や要望に対して、分かりやすく回答してください。
必要に応じて、具体的な例や説明を加えてください。

ユーザーの入力: {user_input}""",
            "evaluation": """以下の構造を評価し、スコアとフィードバックを提供してください。

構造:
{user_input}

評価基準:
1. 意図との一致度
2. 構造の明確さ
3. 実装の容易さ

評価結果は以下のJSON形式で返してください:
{{
  "score": 0-100の数値,
  "feedback": "評価の詳細な説明",
  "details": {{
    "intent_match": "意図との一致度に関する詳細",
    "clarity": "構造の明確さに関する詳細",
    "implementation": "実装の容易さに関する詳細"
  }}
}}""",
            "structure_evaluation": """以下の構成を評価してください。\n\nタイトル: {structure.title}\n説明: {structure.description}\n内容: {structure.content}\n\nこの構成の妥当性を0.0-1.0のスコアで評価し、改善すべき点と理由を述べてください。\n\n構成が未記入、または構成が存在しない場合は、\n「構成が未入力のため、評価できません」とだけ返答してください。\n\n評価結果は以下のJSON形式で返してください:\n{{\n  \"is_valid\": true,\n  \"score\": 0.85,\n  \"feedback\": \"構成は概ね妥当ですが、目的の記載が不足しています。\",\n  \"details\": {{\n    \"intent_match\": \"意図との一致度に関する詳細\",\n    \"clarity\": \"構造の明確さに関する詳細\",\n    \"implementation\": \"実装の容易さに関する詳細\",\n    \"strengths\": [\"強み1\", \"強み2\"],\n    \"weaknesses\": [\"弱み1\", \"弱み2\"],\n    \"suggestions\": [\"改善提案1\", \"改善提案2\"]\n  }}\n}}"""
        }
        
        claude_descriptions = {
            "chat": "Claude用の基本的なチャット応答プロンプト",
            "evaluation": "Claude用の構造評価プロンプト",
            "structure_evaluation": "Claudeによる構成評価テンプレート"
        }
        
        # Gemini用テンプレート
        gemini_templates = {
            "chat": """あなたは親切で丁寧なAIアシスタントです。
ユーザーの質問や要望に対して、分かりやすく回答してください。
必要に応じて、具体的な例や説明を加えてください。

ユーザーの入力: {user_input}""",
            "evaluation": """以下の構造を評価し、スコアとフィードバックを提供してください。

構造:
{user_input}

評価基準:
1. 意図との一致度
2. 構造の明確さ
3. 実装の容易さ

評価結果は以下のJSON形式で返してください:
{{
  "score": 0-100の数値,
  "feedback": "評価の詳細な説明",
  "details": {{
    "intent_match": "意図との一致度に関する詳細",
    "clarity": "構造の明確さに関する詳細",
    "implementation": "実装の容易さに関する詳細"
  }}
}}""",
            "completion": """以下はユーザーの会話とClaudeによる構成評価を元にしたアプリ構成案です。構成の不足点を補完し、必ず下記のJSON形式で出力してください。\n\n## ユーザー入力\n{{ user_input }}\n\n## Claude構成\n{{ structure }}\n\n---\n**出力形式（期待値）:**\n```json\n{{\n  \"title\": \"構成のタイトル\",\n  \"modules\": [\n    {{ \"name\": \"モジュール名\", \"detail\": \"詳細説明\" }}\n    // ... 必要な数だけ繰り返し\n  ]\n}}\n```\n\n**重要:** Claude評価が失敗した場合やClaude構成が空の場合でも、必ず上記のJSON形式（title, modules）で全体構成を出力してください。\n\n**出力ルール:**\n- 必ずJSON形式のみで出力\n- 自然文や説明文は一切含めない\n- コードブロック（```json）で囲む\n- title, modulesは必須フィールド\n- modulesは配列形式で各モジュールにname, detailを含める\n- descriptionは任意フィールド\n- Claude構成が不十分な場合も、推論で全体構成を補完して出力\n- Claude評価が失敗した場合も、ユーザー入力のみから構成を生成し、必ず上記JSON形式で返す\n\n**禁止事項:**\n- 自然文での説明\n- リスト形式や箇条書きでの出力\n- JSON以外の形式\n- コードブロック外での説明\n\n**例:**\n```json\n{{\n  \"title\": \"ブログサイト構成\",\n  \"modules\": [\n    {{ \"name\": \"ヘッダー\", \"detail\": \"ロゴ、ナビゲーション、検索機能を含む\" }},\n    {{ \"name\": \"メインコンテンツ\", \"detail\": \"記事一覧、記事詳細、カテゴリ\" }},\n    {{ \"name\": \"サイドバー\", \"detail\": \"プロフィール、カテゴリ一覧、最新記事\" }},\n    {{ \"name\": \"フッター\", \"detail\": \"コピーライト、リンク\" }}\n  ]\n}}\n```\n\n**最終確認:**\n- 出力は必ずJSON形式のみ\n- 自然文やMarkdownは一切含めない\n- コードブロック（```json）で囲む\n- 有効なJSON構文であることを確認\n\n必ず上記のJSON形式で出力してください。"""
        }
        
        gemini_descriptions = {
            "chat": "Gemini用の基本的なチャット応答プロンプト",
            "evaluation": "Gemini用の構造評価プロンプト",
            "completion": "Gemini用の構成補完プロンプト",
            "structure_evaluation": "Geminiによる構成評価テンプレート"
        }
        
        logger.info("📝 テンプレート辞書作成完了")
        
        # テンプレートを登録
        for provider, templates in [
            ("chatgpt", (chatgpt_templates, chatgpt_descriptions)),
            ("claude", (claude_templates, claude_descriptions)),
            ("gemini", (gemini_templates, gemini_descriptions))
        ]:
            logger.info(f"🔄 {provider} テンプレート登録開始")
            templates_dict, descriptions_dict = templates
            for name, template in templates_dict.items():
                description = descriptions_dict.get(name, "")
                logger.info(f"  📝 {provider}.{name} 登録中...")
                # Promptオブジェクトを作成して登録
                prompt = Prompt(
                    name=name,
                    provider=provider,
                    description=description,
                    template=template
                )
                prompt_manager.register(prompt)
                logger.info(f"  ✅ {provider}.{name} 登録完了")

        logger.info("🔄 基本テンプレート登録完了")

        # 汎用テンプレート（プロバイダー非依存）
        logger.info("🔄 汎用テンプレート登録開始")
        builtin_templates = {
            "claude_check_structure": """以下の構成案について、ユーザーに親しみやすい自然な日本語で確認メッセージを作成してください。

構成案の要点を簡単に含めつつ、「この方向で合っていそうでしょうか？」「よければ、この内容でどんな画面になるか一緒に見てみませんか？」といった、次への導きとなるような言葉を添えてください。
あなたの応答は、ユーザーに表示されるメッセージそのものです。JSONやマークダウンを含めず、自然な文章のみを出力してください。

構成案:
{structure_json}""",
            "structure_from_input": """ユーザーの入力から、以下の情報を含む構成案を自然な文章で提案し、最後にJSON形式で出力してください。

ユーザー入力:
{user_input}

提案のポイント:
- ユーザーの意図を汲み取り、具体的な構成に落とし込む
- 専門用語を避け、分かりやすい言葉で説明する
- 自然な会話のように、確認や提案を投げかける

提案文とJSONは明確に分離してください。

例：
「〇〇というアプリの構成を考えてみました。主な機能は××と△△です。こんな内容でいかがでしょうか？
```json
{{
  "title": "〇〇",
  "description": "...",
  "content": {{ ... }}
}}
```」

それでは、提案を始めてください。"""
        }

        for name, template in builtin_templates.items():
            prompt_manager.builtin_templates[name] = template
            logger.info(f"  📝 汎用テンプレート '{name}' 登録完了")

        logger.info(f"✅ register_all_templates 完了 - 登録済みテンプレート数: {len(prompt_manager.prompts)}, 汎用テンプレート数: {len(prompt_manager.builtin_templates)}")
        
    except Exception as e:
        logger.error(f"❌ テンプレート登録中にエラーが発生: {e}")
        raise

__all__ = ['register_all_templates'] 