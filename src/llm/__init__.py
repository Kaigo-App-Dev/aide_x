"""
LLM Module

このモジュールは、LLM（大規模言語モデル）の機能を提供します。
"""

from typing import List, Dict, Any, Optional
from src.common.types import ChatMessage, AIProviderResponse
from .hub import LLMHub
from .providers.base import BaseLLMProvider
from .providers.claude import ClaudeProvider
from .providers.chatgpt import ChatGPTProvider
from .providers.gemini import GeminiProvider
from .prompts import prompt_manager, PromptManager
from .controller import AIController

__all__ = [
    "BaseLLMProvider",
    "ChatMessage",
    "LLMHub",
    "ClaudeProvider",
    "ChatGPTProvider",
    "GeminiProvider",
    "PromptManager",
    "prompt_manager",
    "AIController"
]

def call_model(
    model: str,
    messages: List[ChatMessage],
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs
) -> AIProviderResponse:
    """
    LLMを呼び出して応答を取得（簡易インターフェース）
    
    Args:
        model (str): モデル名（例: "claude-3-opus", "gemini-pro"）
        messages (List[ChatMessage]): メッセージリスト
        system_prompt (Optional[str]): システムプロンプト
        temperature (float): 温度パラメータ（0.0-1.0）
        max_tokens (int): 最大トークン数
        
    Returns:
        AIProviderResponse: {
            "status": "success" | "error",
            "response": str,  # 成功時
            "error": str      # エラー時
        }
    """
    return call_model(
        model=model,
        messages=messages,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )

def chat_completion(
    messages: List[ChatMessage],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> AIProviderResponse:
    """ChatGPT APIを使用してチャット補完を実行"""
    provider = ChatGPTProvider()
    return provider.chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

"""LLM (Large Language Model) related functionality.""" 