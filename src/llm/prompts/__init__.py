"""
プロンプト管理モジュール

このモジュールは、AIモデル用のプロンプト管理機能を提供します。
"""

from typing import Dict, Any, Optional
from .types import PromptTemplate
from .manager import PromptManager

# シングルトンインスタンスを作成
prompt_manager = PromptManager()

__all__ = ['PromptManager', 'PromptTemplate', 'prompt_manager'] 