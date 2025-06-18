"""
Unified LLM Client
"""

import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional, Union, List, cast
from src.types import LLMResponse, safe_cast_str, safe_cast_dict
from src.llm.controller import AIController
from src.exceptions import AIProviderError, APIRequestError, ResponseFormatError
from src.llm.providers.base import ChatMessage

logger = logging.getLogger(__name__)

# 🔑 .env 読み込み
load_dotenv()

def call_llm(
    messages: List[ChatMessage],
    system_prompt: Optional[str] = None,
    model: str = "claude-3-sonnet-20240229",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    stream: bool = False
) -> LLMResponse:
    """Unified interface for calling LLM providers"""
    try:
        # Add system message if not present
        if system_prompt and not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {
                "role": "system",
                "content": system_prompt
            })

        # Determine provider from model name
        provider = "claude" if model.startswith("claude") else \
                  "gemini" if model.startswith("gemini") else \
                  "chatgpt"

        # Call provider through AIController
        response = AIController.call(
            provider=provider,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream
        )

        return cast(LLMResponse, {
            "role": "assistant",
            "content": safe_cast_str(response.get("content")) or "",
            "status": "success",
            "model": model,
            "usage": safe_cast_dict(response.get("usage"))
        })

    except (APIRequestError, ResponseFormatError) as e:
        logger.error(f"Error calling LLM: {str(e)}")
        return cast(LLMResponse, {
            "role": "assistant",
            "content": "",
            "status": "error",
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Unexpected error calling LLM: {str(e)}")
        return cast(LLMResponse, {
            "role": "assistant",
            "content": "",
            "status": "error",
            "error": str(e)
        })

# ✅ 統一インターフェース client.chat(...) に対応
class UnifiedClient:
    """Unified client for all LLM providers"""
    def __init__(self, model: str = "claude-3-sonnet-20240229"):
        self.model = model

    def call(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> LLMResponse:
        return call_llm(
            messages=messages,
            system_prompt=system_prompt,
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream
        )

# ✅ これを import して使えばOK
client = UnifiedClient()
