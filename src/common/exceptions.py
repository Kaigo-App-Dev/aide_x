"""
共通例外定義
"""

class AIProviderError(Exception):
    """AIプロバイダの基底例外"""
    pass

class ClaudeAPIError(AIProviderError):
    """Exception raised for Claude API errors."""
    pass

class GeminiAPIError(AIProviderError):
    """Exception raised for Gemini API errors."""
    pass

class ChatGPTAPIError(AIProviderError):
    """Exception raised for ChatGPT API errors."""
    pass

class EvaluationError(Exception):
    """評価処理での失敗を示す例外"""
    pass

class PromptNotFoundError(AIProviderError):
    """プロンプトが見つからない場合の例外"""
    pass

class APIRequestError(AIProviderError):
    """APIリクエスト失敗時の例外"""
    pass

class ResponseFormatError(AIProviderError):
    """レスポンスのフォーマットが不正な場合の例外"""
    pass 