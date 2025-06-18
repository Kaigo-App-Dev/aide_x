"""
プロンプトテンプレート管理モジュール
"""

from typing import Dict, Any
from .manager import PromptManager

def register_all_templates(prompt_manager: PromptManager) -> None:
    """すべてのプロンプトテンプレートを登録する"""
    
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
{
  "score": 0-100の数値,
  "feedback": "評価の詳細な説明",
  "details": {
    "intent_match": "意図との一致度に関する詳細",
    "clarity": "構造の明確さに関する詳細",
    "implementation": "実装の容易さに関する詳細"
  }
}"""
    }
    
    chatgpt_descriptions = {
        "chat": "ChatGPT用の基本的なチャット応答プロンプト",
        "evaluation": "ChatGPT用の構造評価プロンプト"
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
{
  "score": 0-100の数値,
  "feedback": "評価の詳細な説明",
  "details": {
    "intent_match": "意図との一致度に関する詳細",
    "clarity": "構造の明確さに関する詳細",
    "implementation": "実装の容易さに関する詳細"
  }
}"""
    }
    
    claude_descriptions = {
        "chat": "Claude用の基本的なチャット応答プロンプト",
        "evaluation": "Claude用の構造評価プロンプト"
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
{
  "score": 0-100の数値,
  "feedback": "評価の詳細な説明",
  "details": {
    "intent_match": "意図との一致度に関する詳細",
    "clarity": "構造の明確さに関する詳細",
    "implementation": "実装の容易さに関する詳細"
  }
}"""
    }
    
    gemini_descriptions = {
        "chat": "Gemini用の基本的なチャット応答プロンプト",
        "evaluation": "Gemini用の構造評価プロンプト"
    }
    
    # テンプレートを登録
    for provider, templates in [
        ("chatgpt", (chatgpt_templates, chatgpt_descriptions)),
        ("claude", (claude_templates, claude_descriptions)),
        ("gemini", (gemini_templates, gemini_descriptions))
    ]:
        templates_dict, descriptions_dict = templates
        for name, template in templates_dict.items():
            description = descriptions_dict.get(name, "")
            prompt_manager.register(provider, name, template, description)

__all__ = ['register_all_templates'] 