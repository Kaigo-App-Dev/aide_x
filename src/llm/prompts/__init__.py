"""
プロンプト管理モジュール

このモジュールは、AIプロバイダー用のプロンプトテンプレートを管理します。
"""

from typing import Dict, Any, Optional
from .types import PromptTemplate
from .manager import PromptManager, Prompt, prompt_manager
from .templates import register_all_templates

# シングルトンインスタンスを作成
prompt_manager = PromptManager()

# 初期化時にテンプレートを登録
import logging
logger = logging.getLogger(__name__)

try:
    logger.info("🔄 プロンプトテンプレート登録開始")
    register_all_templates(prompt_manager)
    logger.info(f"✅ プロンプトテンプレート登録完了 - 登録済み数: {len(prompt_manager.prompts)}")
    logger.info(f"登録済みテンプレート: {list(prompt_manager.prompts.keys())}")
except Exception as e:
    logger.error(f"❌ プロンプトテンプレート登録エラー: {str(e)}")
    import traceback
    traceback.print_exc()

__all__ = ['PromptManager', 'Prompt', 'prompt_manager', 'register_all_templates'] 