"""
OpenAI API utilities
"""

import os
import logging
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

def call_chatgpt_api(prompt: str, system_prompt: str = "") -> str:
    """
    ChatGPT APIを呼び出して応答を返す
    
    Args:
        prompt (str): ユーザーの入力プロンプト
        system_prompt (str, optional): システムプロンプト. デフォルトは空文字列.
    
    Returns:
        str: ChatGPTからの応答テキスト
    
    Raises:
        ValueError: APIキーが設定されていない場合
        Exception: API呼び出し中にエラーが発生した場合
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません")

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"[ChatGPT] API呼び出しエラー: {str(e)}")
        raise

__all__ = ["call_chatgpt_api"] 