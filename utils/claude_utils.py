from utils.llm_client import call_llm

def get_claude_intent_reason(structure: dict) -> dict:
    """
    Claudeに構成テンプレートを送り、評価理由（intent_reason）を取得する。
    """
    system_prompt = (
        "あなたは構成テンプレートを評価するAIアシスタントです。\n"
        "以下のJSONテンプレートを見て、構成がユーザーの目的とどれだけ一致しているかを評価し、"
        "その理由を日本語で簡潔に答えてください。"
    )
    content = structure.get("content", "")

    try:
        response_text = call_llm(
            provider="claude",
            system_prompt=system_prompt,
            user_content=content,
            model="claude-3-opus-20240229",
            max_tokens=1024
        )
        return {
            "intent_reason": response_text
        }
    except Exception as e:
        return {
            "intent_reason": f"[評価失敗] {str(e)}"
        }


# utils/claude_utils.py

def call_claude_api(prompt: str) -> str:
    """
    Claude APIのダミー実装（仮）
    """
    return f"🤖 Claude応答: 『{prompt.strip()}』に対する仮の返答です。"

def get_structure_intent_reason(content_json_str: str) -> str:
    return "Claudeによる構成意図の説明（仮）"
