import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def call_openai(prompt: str, system_prompt: str = "") -> str:
    """
    OpenAI APIを呼び出して応答を取得する
    
    Args:
        prompt (str): プロンプト
        system_prompt (str): システムプロンプト（オプション）
        
    Returns:
        str: OpenAIの応答
    """
    try:
        # TODO: OpenAI APIの実装
        logger.info("[OPENAI] API call not implemented yet")
        return "OpenAI API call not implemented yet"
    except Exception as e:
        logger.error(f"[OPENAI] Error calling API: {str(e)}")
        raise 