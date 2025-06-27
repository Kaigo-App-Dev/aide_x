"""
構造評価モジュール

このモジュールは、AIモデルを使用して構造の評価を行う機能を提供します。
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from src.llm.controller import AIController
if TYPE_CHECKING:
    from src.llm.evaluators.claude_evaluator import ClaudeEvaluator
from src.llm.evaluators.gemini_evaluator import GeminiEvaluator
from src.exceptions import ProviderError, PromptError
from src.llm.controller import controller
from src.llm.prompts.manager import prompt_manager
from src.structure.utils import StructureDict
from src.llm.evaluators.common import EvaluationResult
from src.common.logging_utils import get_logger, log_exception
from src.exceptions import PromptNotFoundError

logger = get_logger(__name__)

def evaluate_structure_with(
    provider_name: str,
    structure: StructureDict,
    model: Optional[str] = None
) -> Optional[EvaluationResult]:
    """
    指定されたプロバイダを使用して構成を評価します。

    Args:
        provider_name: 使用するLLMプロバイダ名 (例: "claude")
        structure: 評価対象の構成
        model: 使用するモデル名 (オプション)

    Returns:
        評価結果 (EvaluationResult) または失敗した場合は None
    """
    logger.info(f"🚀 構成評価開始: プロバイダ={provider_name}, 構成ID={structure.get('id')}")
    try:
        provider = controller.get_provider(provider_name)
        if not provider or not hasattr(provider, 'evaluate'):
            logger.error(f"❌ プロバイダ '{provider_name}' またはその評価機能が見つかりません。")
            return None

        # プロンプトの準備
        prompt_template_name = f"{provider_name}.structure_evaluation"
        try:
            prompt_manager.get_prompt(provider_name, "structure_evaluation")
        except PromptNotFoundError:
            logger.warning(f"⚠️ 評価用プロンプトテンプレート '{prompt_template_name}' が見つかりません。デフォルトの 'claude.structure_evaluation' を使用します。")
            prompt_template_name = "claude.structure_evaluation"
        
        prompt = prompt_manager.format_prompt(prompt_template_name, structure=structure)
        logger.debug(f"📝 生成された評価プロンプト ({prompt_template_name}):\n---\n{prompt}\n---")

        # 評価の実行
        logger.info(f"🧠 {provider_name} で評価を実行中...")
        # `evaluate` メソッドは BaseProvider で型定義されていないため、hasattrでチェック
        if hasattr(provider, "evaluate"):
            evaluation_result = provider.evaluate(prompt, model=model)
        else:
            logger.error(f"❌ プロバイダ '{provider_name}' に 'evaluate' メソッドが存在しません。")
            return None

        if evaluation_result:
            logger.info(f"✅ 評価成功: {evaluation_result}")
        else:
            logger.error("❌ 評価失敗: 評価結果がNoneです。")

        return evaluation_result

    except Exception as e:
        log_exception(logger, e, f"構成評価処理 (プロバイダ: {provider_name})")
        return None 