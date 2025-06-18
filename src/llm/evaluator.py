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

logger = logging.getLogger(__name__)

class EvaluationResult:
    """評価結果を表すクラス"""
    
    def __init__(self, is_valid: bool, score: float = 0.0, error: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        評価結果の初期化
        
        Args:
            is_valid (bool): 評価が有効かどうか
            score (float): 評価スコア（0.0-1.0）
            error (Optional[str]): エラーメッセージ（エラー時のみ）
            details (Optional[Dict[str, Any]]): 詳細情報（プロンプト、トークン数など）
        """
        self.is_valid = is_valid
        self.score = score
        self.error = error
        self.details = details or {}

def evaluate_structure_with(
    structure: dict,
    provider_name: str = "claude",
    fallback: bool = True
) -> Optional[EvaluationResult]:
    """
    指定されたプロバイダーを使用して構造を評価
    
    Args:
        structure (dict): 評価対象の構造
        provider_name (str): 使用するプロバイダー名（"claude" または "gemini"）
        fallback (bool): Claude失敗時にGeminiにフォールバックするかどうか
        
    Returns:
        Optional[EvaluationResult]: 評価結果。失敗時はNone
        
    Raises:
        ValueError: 無効なプロバイダー名が指定された場合
    """
    if provider_name not in ["claude", "gemini"]:
        raise ValueError(f"Invalid provider name: {provider_name}")
    
    # 最初のプロバイダーで評価を試みる
    try:
        if provider_name == "claude":
            evaluator: 'ClaudeEvaluator' = ClaudeEvaluator()
            result = evaluator.evaluate(structure)
            if result.is_valid:
                logger.debug(f"[CLAUDE] 評価成功: score={result.score}, valid={result.is_valid}")
                return result
            logger.debug(f"[CLAUDE] 評価失敗: {result.error}")
        else:
            evaluator = GeminiEvaluator()
            result = evaluator.evaluate(structure)
            if result.is_valid:
                logger.debug(f"[GEMINI] 評価成功: score={result.score}, valid={result.is_valid}")
                return result
            logger.debug(f"[GEMINI] 評価失敗: {result.error}")
    except (ProviderError, PromptError) as e:
        logger.debug(f"[{provider_name.upper()}] 評価失敗: {str(e)}")
    
    # フォールバックが有効で、最初のプロバイダーがClaudeの場合
    if fallback and provider_name == "claude":
        try:
            evaluator = GeminiEvaluator()
            result = evaluator.evaluate(structure)
            if result.is_valid:
                logger.debug(f"[GEMINI] 評価成功 (fallback): score={result.score}, valid={result.is_valid}")
                return result
            logger.debug(f"[GEMINI] 評価失敗 (fallback): {result.error}")
        except (ProviderError, PromptError) as e:
            logger.debug(f"[GEMINI] 評価失敗 (fallback): {str(e)}")
    
    return None 