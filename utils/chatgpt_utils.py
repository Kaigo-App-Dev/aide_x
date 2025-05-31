import json
from utils.llm_client import call_llm

def generate_improvement(structure: dict) -> dict:
    """
    構成テンプレートに対して改善案を生成する（ChatGPT使用、LLMクライアント経由）
    """
    system_prompt = "以下の構成テンプレートをより良く改善してください。JSON形式の構造は維持してください。"
    user_input = f"構成:\n{structure.get('content', '')}"

    # ChatGPTへ送信
    response_text = call_llm(
        provider="gpt",
        system_prompt=system_prompt,
        user_content=user_input,
        model="gpt-4",
        max_tokens=1500
    )

    try:
        improved_data = json.loads(response_text)
    except Exception as e:
        raise ValueError(f"改善案のパースに失敗しました: {e}\n出力内容:\n{response_text}")

    # メタ情報を付加
    improved_data["title"] = structure.get("title", "No Title")
    improved_data["id"] = structure["id"] + "_evolved"

    return improved_data


# utils/chatgpt_utils.py

def call_chatgpt_api(prompt: str) -> str:
    """
    ChatGPTのAPI呼び出し（仮実装）
    """
    return f"💬 ChatGPT応答: 『{prompt.strip()}』に対する仮の返答です。"
