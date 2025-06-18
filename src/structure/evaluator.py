"""
構造評価モジュール

このモジュールは、構造の評価機能を提供します。
"""

import json
import logging
from typing import Dict, Any, Optional, List
from src.llm.controller import AIController
from src.llm.providers.base import ChatMessage
from src.llm.prompts import prompt_manager, PromptManager
from src.common.exceptions import AIProviderError, APIRequestError, ResponseFormatError
from src.common.types import EvaluationResult
from src.common.utils import extract_json_part
from src.llm.hub import call_model

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

def evaluate_structure(
    structure: str,
    provider: str = "claude",
    prompt_manager: Optional[PromptManager] = None
) -> EvaluationResult:
    """
    構造を評価
    
    Args:
        structure (str): 評価対象の構造
        provider (str): 使用するプロバイダー（"claude" または "gemini"）
        prompt_manager (Optional[PromptManager]): プロンプトマネージャー
        
    Returns:
        EvaluationResult: 評価結果
    """
    if prompt_manager is None:
        from src.llm.prompts import prompt_manager as global_prompt_manager
        prompt_manager = global_prompt_manager
        prompt_manager.register_builtin_templates()
    else:
        prompt_manager.register_builtin_templates()
    
    template = prompt_manager.get_prompt("evaluation", provider)
    if template is None:
        logger.error(f"Provider {provider} does not have an evaluation template")
        return EvaluationResult(
            score=0.0,
            feedback=f"プロバイダー {provider} の評価用テンプレートが見つかりません",
            details={},
            is_valid=False
        )
    
    try:
        prompt = template.template.format(user_input=structure)
    except KeyError as e:
        logger.error(f"Template format error: {str(e)}")
        return EvaluationResult(
            score=0.0,
            feedback=f"プロンプトのフォーマットエラー: {str(e)}",
            details={},
            is_valid=False
        )
    
    try:
        # モデルを呼び出して評価を実行
        response = call_model(provider, prompt)
        
        # レスポンスの検証
        if not response or "content" not in response:
            logger.error("Empty response from model")
            return EvaluationResult(
                score=0.0,
                feedback="評価結果が空です",
                details={},
                is_valid=False
            )
        
        # レスポンスからJSONを抽出
        result_json = extract_json_part(response.get("content", ""))
        if not result_json:
            logger.error("Failed to extract JSON from response")
            return EvaluationResult(
                score=0.0,
                feedback="評価結果の解析に失敗しました",
                details={},
                is_valid=False
            )
        
        # 必須フィールドの確認
        required_fields = ["score", "feedback", "details"]
        if not all(field in result_json for field in required_fields):
            logger.error(f"Missing required fields in result: {[f for f in required_fields if f not in result_json]}")
            return EvaluationResult(
                score=0.0,
                feedback="評価結果に必須フィールドが含まれていません",
                details={},
                is_valid=False
            )
        
        # 評価結果を構築
        return EvaluationResult(
            score=float(result_json["score"]),
            feedback=str(result_json["feedback"]),
            details=dict(result_json["details"]),
            is_valid=True
        )
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return EvaluationResult(
            score=0.0,
            feedback=f"評価中にエラーが発生しました: {str(e)}",
            details={},
            is_valid=False
        )

def evaluate_structure_with(model_name: str, structure: Dict[str, Any], prompt_manager: Optional[PromptManager] = None) -> EvaluationResult:
    """
    指定されたモデルを使用して構造を評価する
    
    Args:
        model_name (str): 使用するモデル名 ("claude" または "gemini")
        structure (Dict[str, Any]): 評価対象の構造
        prompt_manager (Optional[PromptManager]): プロンプトマネージャー
        
    Returns:
        EvaluationResult: 評価結果
        
    Raises:
        ValueError: 無効なモデル名が指定された場合
    """
    if model_name not in ["claude", "gemini"]:
        raise ValueError(f"Unsupported model: {model_name}")
    
    if prompt_manager is None:
        from src.llm.prompts import prompt_manager as global_prompt_manager
        prompt_manager = global_prompt_manager
    prompt_manager.register_builtin_templates()
    
    template = prompt_manager.get_prompt("evaluation", model_name)
    if not template or not isinstance(template.template, str):
        return EvaluationResult(
            score=0.0,
            feedback="評価用プロンプトが見つかりません",
            details={},
            is_valid=False
        )
    
    # 構造をJSON文字列に変換
    structure_json = json.dumps(structure, ensure_ascii=False, indent=2)
    
    # プロンプトの置換
    try:
        prompt = template.template.format(user_input=structure_json)
    except KeyError as e:
        logger.error(f"Template format error: {str(e)}")
        return EvaluationResult(
            score=0.0,
            feedback=f"プロンプトのフォーマットエラー: {str(e)}",
            details={},
            is_valid=False
        )
    
    try:
        # モデルの呼び出し
        response = call_model(model_name, prompt)
        
        # レスポンスの解析
        if not response or "content" not in response:
            return EvaluationResult(
                score=0.0,
                feedback="評価結果が空です",
                details={},
                is_valid=False
            )
        
        # JSONの抽出と解析
        try:
            result = json.loads(response["content"])
        except json.JSONDecodeError:
            return EvaluationResult(
                score=0.0,
                feedback="評価結果の解析に失敗しました",
                details={},
                is_valid=False
            )
        
        # 必須フィールドの確認
        required_fields = ["score", "feedback", "details"]
        if not all(field in result for field in required_fields):
            return EvaluationResult(
                score=0.0,
                feedback="評価結果に必須フィールドが含まれていません",
                details={},
                is_valid=False
            )
        
        # 評価結果の作成
        return EvaluationResult(
            score=float(result["score"]),
            feedback=str(result["feedback"]),
            details=dict(result["details"]),
            is_valid=True
        )
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return EvaluationResult(
            score=0.0,
            feedback=f"評価中にエラーが発生しました: {str(e)}",
            details={},
            is_valid=False
        )

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
        return evaluate_structure_with("claude", structure)
    except Exception as e:
        logger.warning(f"Claude evaluation failed, falling back to Gemini: {str(e)}")
        return evaluate_structure_with("gemini", structure) 