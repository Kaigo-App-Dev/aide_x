import os
import logging
from typing import Dict, Any, Optional, Union, List
from src.common.types import LLMResponse, ChatMessage

logger = logging.getLogger(__name__)

def call_cursor_api(
    messages: List[ChatMessage],
    model: str = "claude-3-opus",
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> LLMResponse:
    """
    Cursor APIを呼び出して応答を取得する
    
    Args:
        messages (List[ChatMessage]): メッセージリスト
        model (str): 使用するモデル名
        temperature (float): 温度パラメータ
        max_tokens (int): 最大トークン数
        
    Returns:
        LLMResponse: Cursorからの応答
    """
    try:
        # TODO: 実際のCursor API呼び出しを実装
        return {
            "role": "assistant",
            "content": "Response from Cursor API",
            "status": "success",
            "error": None,
            "model": model,
            "usage": {}
        }
    except Exception as e:
        return {
            "role": "assistant",
            "content": f"[エラー] {str(e)}",
            "status": "error",
            "error": str(e),
            "model": model,
            "usage": {}
        }

def format_cursor_messages(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    """
    Cursor用にメッセージをフォーマットする
    
    Args:
        messages (List[ChatMessage]): フォーマット対象のメッセージ
        
    Returns:
        List[Dict[str, str]]: フォーマットされたメッセージ
    """
    formatted = []
    for msg in messages:
        formatted.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    return formatted

def parse_cursor_response(response: Union[str, Dict[str, Any]]) -> LLMResponse:
    """
    Cursorの応答をパースする
    
    Args:
        response (Union[str, Dict[str, Any]]): パース対象の応答
        
    Returns:
        LLMResponse: パースされた応答
    """
    if isinstance(response, str):
        return {
            "role": "assistant",
            "content": response,
            "status": "success"
        }
    elif isinstance(response, dict):
        return {
            "role": "assistant",
            "content": response.get("content", ""),
            "status": response.get("status", "success"),
            "error": response.get("error")
        }
    else:
        return {
            "role": "assistant",
            "content": str(response),
            "status": "success"
        } 