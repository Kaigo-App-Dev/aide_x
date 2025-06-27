"""
AIコントローラー

このモジュールは、AIプロバイダーの管理とリクエストの制御を行います。
"""

from typing import Dict, Any, Optional, List, Union
import logging
import os
from enum import Enum
from dotenv import load_dotenv
import json
from .providers.base import BaseLLMProvider, ChatMessage
from .providers.chatgpt import ChatGPTProvider
from .providers.claude import ClaudeProvider
from .providers.gemini import GeminiProvider
from .prompts import prompt_manager
from src.exceptions import AIProviderError, ResponseFormatError
from src.llm.prompts.manager import PromptManager
from src.types import LLMResponse, AIProviderResponse, StructureDict, EvaluationResult

# ✅ テスト環境向けダミーAPIキーを未設定時に補完
os.environ.setdefault("GOOGLE_API_KEY", "dummy_key")
os.environ.setdefault("CLAUDE_API_KEY", "dummy_key")
os.environ.setdefault("OPENAI_API_KEY", "dummy_key")

logger = logging.getLogger(__name__)

class AIProviderType(Enum):
    """AIプロバイダの種類"""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"

class AIController:
    """AIコントローラークラス"""
    
    def __init__(self, prompt_manager: PromptManager):
        """
        AIControllerの初期化
        
        Args:
            prompt_manager (PromptManager): プロンプト管理インスタンス（必須）
            
        Raises:
            ValueError: prompt_managerが指定されていない場合
        """
        if prompt_manager is None:
            raise ValueError("PromptManager instance is required")
        self.prompt_manager = prompt_manager
        self._providers: Dict[str, Any] = {}
        self.failed_providers: Dict[str, str] = {}
        logger.info("AIControllerを初期化しました")

    def register_provider(self, name: str, provider: Any) -> None:
        """AIプロバイダを登録する"""
        self._providers[name] = provider
        logger.info(f"✅ {name}プロバイダを登録しました")

    def _call(self, provider: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """指定したプロバイダを使用してAIを呼び出す（インスタンスメソッド）"""
        if provider not in self._providers:
            if provider in self.failed_providers:
                raise AIProviderError(f"プロバイダ '{provider}' は初期化に失敗しています: {self.failed_providers[provider]}")
            raise AIProviderError(f"プロバイダ '{provider}' は登録されていません")
        
        try:
            # プロバイダーのcallメソッドを呼び出し
            response = self._providers[provider].call(messages, **kwargs)
            
            # レスポンスの処理
            if isinstance(response, dict):
                return response.get("content", "")
            else:
                return str(response) if response is not None else ""
                
        except Exception as e:
            logger.error(f"❌ {provider}プロバイダの呼び出しに失敗: {str(e)}")
            raise AIProviderError(f"AI呼び出しエラー: {str(e)}")

    @staticmethod
    def call(provider: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """静的メソッドとしてAIを呼び出す"""
        return controller._call(provider, messages, **kwargs)

    def get_provider(self, provider_name: str) -> Optional[Any]:
        """
        指定されたプロバイダーのインスタンスを取得
        
        Args:
            provider_name (str): プロバイダー名（'chatgpt', 'claude', 'gemini'）
            
        Returns:
            Optional[Any]: プロバイダーインスタンス、存在しない場合はNone
        """
        providers = {
            'chatgpt': ChatGPTProvider,
            'claude': ClaudeProvider,
            'gemini': GeminiProvider
        }
        
        provider_class = providers.get(provider_name.lower())
        if not provider_class:
            logger.error(f"Unknown provider: {provider_name}")
            return None
        
        try:
            return provider_class(prompt_manager=self.prompt_manager)
        except Exception as e:
            logger.error(f"Failed to initialize provider {provider_name}: {str(e)}")
            return None
    
    def generate_response(self, provider_name: str, prompt: str, **kwargs) -> str:
        """
        指定されたプロバイダーを使用して応答を生成
        
        Args:
            provider_name (str): プロバイダー名
            prompt (str): 入力プロンプト
            **kwargs: 追加のパラメータ
            
        Returns:
            str: 生成された応答
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return f"Error: Provider {provider_name} not found"
        
        try:
            return provider.generate_response(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Error generating response from {provider_name}: {str(e)}")
            return f"Error: {str(e)}"

def create_controller() -> AIController:
    """コントローラーのインスタンスを作成し、プロバイダを登録する"""
    # .envファイルの読み込みを保証
    load_dotenv()
    
    # プロバイダのインポート
    from src.llm.providers.chatgpt import ChatGPTProvider
    from src.llm.providers.claude import ClaudeProvider
    from src.llm.providers.gemini import GeminiProvider

    controller = AIController(prompt_manager=prompt_manager)

    # AIプロバイダーの初期化
    chatgpt_provider = ChatGPTProvider(prompt_manager=prompt_manager)
    claude_provider = ClaudeProvider(prompt_manager=prompt_manager)
    gemini_provider = GeminiProvider(prompt_manager=prompt_manager)

    # ChatGPTプロバイダの登録
    try:
        controller.register_provider("chatgpt", chatgpt_provider)
    except Exception as e:
        logger.error(f"❌ ChatGPTプロバイダ登録失敗: {str(e)}")
        controller.failed_providers["chatgpt"] = str(e)

    # Claudeプロバイダの登録
    try:
        controller.register_provider("claude", claude_provider)
    except Exception as e:
        logger.error(f"❌ Claudeプロバイダ登録失敗: {str(e)}")
        controller.failed_providers["claude"] = str(e)

    # Geminiプロバイダの登録
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEYが設定されていません")
        controller.register_provider("gemini", gemini_provider)
    except Exception as e:
        logger.error(f"❌ Geminiプロバイダ登録失敗: {str(e)}")
        controller.failed_providers["gemini"] = str(e)

    return controller

# グローバル変数として遅延定義
controller = create_controller()

__all__ = ["controller", "AIController", "AIProviderType"] 