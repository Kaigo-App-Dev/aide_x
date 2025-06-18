"""
構造評価モジュール

このモジュールは、構造の評価機能を提供します。
"""

import json
import logging
from typing import Dict, Any, Optional, List, cast, Union, TYPE_CHECKING
from src.llm.controller import AIController
from src.llm.providers.base import ChatMessage
from src.llm.prompts import prompt_manager, PromptManager
from src.exceptions import AIProviderError, APIRequestError, ResponseFormatError, EvaluationError
from src.types import EvaluationResult, StructureDict
from src.utils.files import extract_json_part
from src.llm.hub import call_model
if TYPE_CHECKING:
    from src.llm.evaluators.claude_evaluator import ClaudeEvaluator

logger = logging.getLogger(__name__)

def validate_evaluation_result(result_dict: Dict[str, Any]) -> EvaluationResult:
    """
    評価結果のバリデーション
    
    Args:
        result_dict: 評価結果の辞書
        
    Returns:
        EvaluationResult: バリデーション済みの評価結果
    """
    # 必須フィールドのチェック
    required_fields = {
        "score": float,
        "feedback": str,
        "details": dict
    }
    
    missing_fields = []
    for field, field_type in required_fields.items():
        if field not in result_dict:
            missing_fields.append(field)
            continue
        
        # 型チェック
        if not isinstance(result_dict[field], field_type):
            missing_fields.append(field)
    
    if missing_fields:
        logger.warning(f"Missing required fields in evaluation result: {missing_fields}")
        return EvaluationResult(
            is_valid=False,
            score=0.0,
            feedback="Missing required fields in evaluation result",
            details={}
        )
    
    return EvaluationResult(
        is_valid=True,
        score=result_dict["score"],
        feedback=result_dict["feedback"],
        details=result_dict["details"]
    )

def evaluate_structure(structure: Dict[str, Any]) -> EvaluationResult:
    """
    構造を評価する
    
    Args:
        structure: 評価対象の構造
        
    Returns:
        EvaluationResult: 評価結果
    """
    # 構造をStructureDictに変換
    structure_dict = cast(StructureDict, structure)
    
    try:
        # プロンプトの取得と実行
        prompt = prompt_manager.get("evaluation")
        response = call_model(prompt, structure_dict)
        
        # レスポンスの解析
        if not response or not isinstance(response, dict):
            return {
                "score": 0.0,
                "feedback": "評価結果が空です",
                "details": {},
                "is_valid": False
            }
        
        # 評価結果の抽出
        result = extract_json_part(response.get("content", ""))
        if not result:
            return {
                "score": 0.0,
                "feedback": "評価結果の解析に失敗しました",
                "details": {},
                "is_valid": False
            }
        
        # 必須フィールドの確認
        required_fields = ["score", "feedback", "details", "is_valid"]
        if not all(field in result for field in required_fields):
            return {
                "score": 0.0,
                "feedback": "評価結果に必須フィールドが含まれていません",
                "details": {},
                "is_valid": False
            }
        
        # 評価結果の型変換
        return {
            "score": float(result["score"]),
            "feedback": str(result["feedback"]),
            "details": dict(result["details"]),
            "is_valid": bool(result["is_valid"])
        }
        
    except Exception as e:
        logger.error(f"評価中にエラーが発生: {str(e)}")
        return {
            "score": 0.0,
            "feedback": f"評価中にエラーが発生しました: {str(e)}",
            "details": {},
            "is_valid": False
        }

def evaluate_structure_with(provider_name: str, structure: dict) -> EvaluationResult:
    """
    指定したプロバイダで構造を評価する
    Args:
        provider_name: 使用するプロバイダ名
        structure: 評価対象の構造
    Returns:
        EvaluationResult: 評価結果
    """
    try:
        model_name = "claude-3-opus-20240229" if provider_name == "claude" else "gemini-pro"
        prompt_name = "structure_evaluation"
        response = call_model(
            provider_name,
            model_name,
            prompt_name,
            prompt_manager,
            structure=structure
        )
        if not response:
            return {
                "score": 0.0,
                "feedback": "評価結果が空です",
                "details": {},
                "is_valid": False
            }
        result = extract_json_part(response)
        if not result:
            return {
                "score": 0.0,
                "feedback": "評価結果の解析に失敗しました",
                "details": {},
                "is_valid": False
            }
        if not (isinstance(result, dict) and "score" in result and isinstance(result["score"], float)
                and "is_valid" in result and isinstance(result["is_valid"], bool)
                and "feedback" in result and isinstance(result["feedback"], str)
                and "details" in result and isinstance(result["details"], dict)):
            raise ValueError("Invalid result format")
        return {
            "score": float(result["score"]),
            "feedback": str(result["feedback"]),
            "details": dict(result["details"]),
            "is_valid": bool(result["is_valid"])
        }
    except Exception as e:
        logger.error(f"評価中にエラーが発生: {str(e)}")
        return {
            "score": 0.0,
            "feedback": f"評価中にエラーが発生しました: {str(e)}",
            "details": {},
            "is_valid": False
        }

def evaluate_structure_fallback(
    structure: Dict[str, Any],
    api_caller: Optional[Any] = None
) -> EvaluationResult:
    """
    構造を評価（Claudeを優先、失敗時はGeminiにフォールバック）
    
    Args:
        structure: 評価する構造
        api_caller: API呼び出し用のオブジェクト（テスト用）
        
    Returns:
        EvaluationResult: 評価結果
    """
    try:
        # ClaudeEvaluatorを使用して評価
        evaluator = ClaudeEvaluator(prompt_manager=prompt_manager)
        result = evaluator.evaluate(structure)
        if result.is_valid:
            return {
                "score": result.score,
                "feedback": result.details.get("feedback", ""),
                "details": result.details,
                "is_valid": result.is_valid
            }
        raise EvaluationError("Claude evaluation failed")
    except Exception as e:
        logger.warning(f"Claude evaluation failed, falling back to Gemini: {str(e)}")
        return evaluate_structure_with("gemini", structure) 