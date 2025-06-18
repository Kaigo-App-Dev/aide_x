"""
例外定義

このモジュールは、アプリケーション全体で使用される例外クラスを定義します。
"""

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

class ProviderError(Exception):
    """プロバイダー関連の基本例外クラス"""
    pass

class ProviderInitializationError(ProviderError):
    """プロバイダーの初期化に失敗した場合の例外"""
    def __init__(self, provider: str, reason: str):
        self.provider = provider
        self.reason = reason
        super().__init__(f"Failed to initialize {provider} provider: {reason}")

class APIKeyMissingError(ProviderError):
    """APIキーが見つからない場合の例外"""
    def __init__(self, provider: str, env_vars: list[str]):
        self.provider = provider
        self.env_vars = env_vars
        super().__init__(
            f"API key not found for {provider} provider. "
            f"Please set one of the following environment variables: {', '.join(env_vars)}"
        ) 