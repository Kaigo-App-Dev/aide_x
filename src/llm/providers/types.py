"""Type definitions for AI providers."""

from typing import Optional, Any

class AIProviderResponse:
    """Response from an AI provider."""
    
    def __init__(
        self,
        content: str,
        raw: Optional[Any] = None,
        provider: str = "",
        error: Optional[str] = None
    ):
        self.content = content
        self.raw = raw
        self.provider = provider
        self.error = error 