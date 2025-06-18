import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def call_mistral(prompt: str, system_prompt: str = "") -> str:
    """
    Mistral APIを呼び出して応答を取得する
    
    Args:
        prompt (str): プロンプト
        system_prompt (str): システムプロンプト（オプション）
        
    Returns:
        str: Mistralの応答
    """
    try:
        # TODO: Mistral APIの実装
        logger.info("[MISTRAL] API call not implemented yet")
        return "Mistral API call not implemented yet"
    except Exception as e:
        logger.error(f"[MISTRAL] Error calling API: {str(e)}")
        raise 