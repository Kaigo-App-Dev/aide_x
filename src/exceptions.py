"""
例外クラス定義

このモジュールは、AIDE-X全体で使用される例外クラスを提供します。
"""

from typing import List

class PromptError(Exception):
    """プロンプト関連の基本例外クラス"""
    pass

class PromptNotFoundError(PromptError):
    """プロンプトが見つからない場合の例外"""
    def __init__(self, provider: str, template_name: str):
        self.provider = provider
        self.template_name = template_name
        super().__init__(f"Prompt template '{template_name}' not found for provider '{provider}'")

class TemplateFormatError(PromptError):
    """テンプレートのフォーマットが不正な場合の例外"""
    def __init__(self, provider: str, template_name: str, error: str):
        self.provider = provider
        self.template_name = template_name
        self.error = error
        super().__init__(f"Template format error in '{template_name}' for provider '{provider}': {error}")

class AIError(Exception):
    """AI関連の基本例外クラス"""
    pass

class AIProviderError(AIError):
    """Raised when the AI provider fails to respond properly."""
    pass

class ProviderError(AIError):
    """プロバイダー固有の例外"""
    pass

class ProviderInitializationError(ProviderError):
    """プロバイダーの初期化に失敗した場合の例外"""
    def __init__(self, provider: str, reason: str):
        self.provider = provider
        self.reason = reason
        super().__init__(f"Failed to initialize {provider} provider: {reason}")

class APIKeyMissingError(ProviderError):
    """APIキーが見つからない場合の例外"""
    def __init__(self, provider: str, env_vars: List[str]):
        self.provider = provider
        self.env_vars = env_vars
        super().__init__(
            f"API key not found for {provider} provider. "
            f"Please set one of the following environment variables: {', '.join(env_vars)}"
        )

class ClaudeAPIError(ProviderError):
    """Claude APIエラー用例外"""
    pass

class GeminiAPIError(ProviderError):
    """Gemini APIエラー用例外"""
    pass

class ChatGPTAPIError(ProviderError):
    """ChatGPT APIエラー用例外"""
    pass

class EvaluationError(AIError):
    """評価関連の例外"""
    pass

class ResponseFormatError(AIError):
    """Raised when the AI provider returns an unexpected format."""
    pass

class APIRequestError(AIError):
    """Raised when an API request fails."""
    pass

__all__ = [
    'AIError',
    'AIProviderError',
    'ProviderError',
    'EvaluationError',
    'ResponseFormatError',
    'PromptNotFoundError',
    'APIRequestError'
] 