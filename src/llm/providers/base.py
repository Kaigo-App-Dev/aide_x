"""
Base classes for LLM providers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.llm.prompts.manager import PromptManager

@dataclass
class ChatMessage:
    """チャットメッセージを表すクラス"""
    role: str
    content: str

@dataclass
class AIProviderResponse:
    """AIプロバイダーの応答を表すクラス"""
    content: Any
    raw: Any
    provider: str
    error: Optional[str] = None

class BaseLLMProvider(ABC):
    """LLMプロバイダーの基本クラス"""
    
    def __init__(self, model: str):
        """
        初期化
        
        Args:
            model: 使用するモデル名
        """
        self.model = model
    
    @abstractmethod
    def chat(
        self,
        messages: List[ChatMessage],
        prompt_manager: Optional['PromptManager'] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        チャットを実行して応答を取得
        
        Args:
            messages: チャットメッセージのリスト
            prompt_manager: プロンプト管理インスタンス
            temperature: 生成の多様性を制御するパラメータ（0.0-1.0）
            max_tokens: 生成する最大トークン数
            
        Returns:
            str: 生成された応答
        """
        pass 

    def call(self, prompt: str, **kwargs) -> AIProviderResponse:
        """APIを呼び出して応答を返す"""
        raise NotImplementedError("Subclasses must implement call()") 