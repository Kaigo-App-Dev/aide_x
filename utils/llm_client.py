import os
import openai
import requests
import anthropic

openai.api_key = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def call_llm(provider: str, system_prompt: str, user_content: str, model: str = None, max_tokens: int = 1000) -> str:
    """
    ChatGPT または Claude にプロンプトを送って応答を返す。
    """
    if provider == "gpt":
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        response = openai.ChatCompletion.create(
            model=model or "gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    elif provider == "claude":
        messages = [
            {"role": "user", "content": f"{system_prompt}\n\n{user_content}"}
        ]
        response = claude_client.messages.create(
            model=model or "claude-3-opus-20240229",
            max_tokens=max_tokens,
            temperature=0.5,
            messages=messages
        )
        return response.content[0].text.strip()

    else:
        raise ValueError(f"不明な provider: {provider}")
