"""
LLM Module

このモジュールは、LLM（大規模言語モデル）の機能を提供します。
"""

from typing import List, Dict, Any, Optional
from src.llm.providers.base import ChatMessage
from src.types import AIProviderResponse, StructureDict, EvaluationResult
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
    provider: Optional[str] = None,
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
        provider (Optional[str]): プロバイダー名（指定がない場合はモデル名から自動判定）
        
    Returns:
        AIProviderResponse: {
            "content": str,  # 実際の生成結果
            "raw": Optional[Dict[str, Any]],  # 元のレスポンス全文（任意）
            "provider": Optional[str],  # "claude", "gemini", "chatgpt" など
            "error": Optional[str],  # エラーメッセージ（任意）
            "model": Optional[str],  # 使用したモデル名
            "usage": Optional[Dict[str, Any]]  # トークン数やコスト情報
        }
    """
    # プロバイダーが指定されていない場合はモデル名から判定
    if not provider:
        if "claude" in model.lower():
            provider = "claude"
        elif "gemini" in model.lower():
            provider = "gemini"
        elif "gpt" in model.lower():
            provider = "chatgpt"
        else:
            raise ValueError(f"Unknown model: {model}")

    # ChatMessageをDict[str, str]に変換
    formatted_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    try:
        response = AIController.call(
            provider=provider,
            messages=formatted_messages,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return {
            "content": response,
            "raw": None,
            "provider": provider,
            "error": None,
            "model": model,
            "usage": None
        }
    except Exception as e:
        return {
            "content": "",
            "raw": None,
            "provider": provider,
            "error": str(e),
            "model": model,
            "usage": None
        }

def chat_completion(
    messages: List[ChatMessage],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> AIProviderResponse:
    """ChatGPT APIを使用してチャット補完を実行"""
    provider = ChatGPTProvider(prompt_manager=prompt_manager)
    response = provider.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return {
        "content": response,
        "raw": None,
        "provider": "chatgpt",
        "error": None,
        "model": model,
        "usage": None
    }

"""LLM (Large Language Model) related functionality.""" 