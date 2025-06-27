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

**重要**: 以下の形式で必ずJSON形式で構成を出力してください。自然文での説明、リスト形式、その他の形式は一切含めないでください。

```json
{{
  "title": "構成タイトル",
  "description": "構成の説明（任意）",
  "content": {{
    "セクション名": {{
      "項目": "内容"
    }}
  }}
}}
```

**出力ルール**:
1. 必ずJSON形式のみで出力
2. 自然文での説明は一切含めない
3. リスト形式や箇条書きは使用しない
4. コードブロック（```json）で囲む
5. titleとcontentは必須フィールド
6. descriptionは任意フィールド
7. キー名は日本語でも英語でも可
8. 値は文字列、数値、真偽値、配列、オブジェクトのいずれか

**禁止事項**:
- 自然文での説明
- リスト形式での出力
- 箇条書きでの出力
- JSON以外の形式
- コードブロック外での説明

**例示**:
ユーザーが「ブログサイトの構成を作成してください」と言った場合：

```json
{{
  "title": "ブログサイト構成",
  "description": "個人ブログサイトの基本構成",
  "content": {{
    "ヘッダー": {{
      "ロゴ": "サイトロゴ",
      "ナビゲーション": "メニュー項目",
      "検索機能": "検索ボックス"
    }},
    "メインコンテンツ": {{
      "記事一覧": "最新記事の表示",
      "記事詳細": "個別記事ページ",
      "カテゴリ": "記事分類"
    }},
    "サイドバー": {{
      "プロフィール": "著者情報",
      "カテゴリ一覧": "カテゴリメニュー",
      "最新記事": "最新記事リスト"
    }},
    "フッター": {{
      "コピーライト": "著作権表示",
      "リンク": "関連リンク"
    }}
  }}
}}
```

**最終確認**:
- 出力は必ずJSON形式のみ
- 自然文やMarkdownは一切含めない
- コードブロック（```json）で囲む
- 有効なJSON構文であることを確認

必ず上記のJSON形式で出力してください。"""
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