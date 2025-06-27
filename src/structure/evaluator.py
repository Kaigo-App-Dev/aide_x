"""
構造評価モジュール

このモジュールは、構造データの評価機能を提供します。
"""

import json
import logging
from typing import Dict, Any, Optional, List, cast, Union, TYPE_CHECKING
from src.llm.controller import AIController
from src.llm.providers.base import ChatMessage
from src.llm.prompts import prompt_manager, PromptManager
from src.exceptions import AIProviderError, APIRequestError, ResponseFormatError, EvaluationError
from src.common.types import EvaluationResult, StructureDict
from src.utils.files import extract_json_part
from src.llm.hub import call_model
from src.structure.history_manager import save_structure_history
if TYPE_CHECKING:
    from src.llm.evaluators.claude_evaluator import ClaudeEvaluator

logger = logging.getLogger(__name__)

def get_prompt_manager() -> PromptManager:
    """プロンプトマネージャーを取得"""
    return prompt_manager

def get_model_for_provider(provider: str) -> str:
    """プロバイダーに対応するモデル名を取得"""
    models = {
        "claude": "claude-3-opus-20240229",
        "gemini": "gemini-pro",
        "chatgpt": "gpt-4"
    }
    return models.get(provider, "claude-3-opus-20240229")

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

def evaluate_structure_with(
    structure: Dict[str, Any],
    provider: str = "claude",
    prompt_manager: Optional[Any] = None
) -> Any:
    """
    構成（単一カードまたは複数カード）をAIで評価し、全体およびカード単位の評価結果を返す
    """
    logger = logging.getLogger(__name__)
    pm = prompt_manager

    # 構成が複数カード（list）か単一カード（dict）かを判定
    content = structure.get("content")
    is_multi = isinstance(content, list)
    card_results = []
    total_score = 0.0
    all_valid = True
    feedbacks = []

    if is_multi:
        # 複数カード（リスト）
        for idx, card in enumerate(content):
            # 各カードの必須フィールドチェック
            if not card.get("title") or not card.get("content"):
                logger.warning(f"⚠️ カード{idx}の必須フィールド（title, content）が不足しています")
                card_result = {
                    "score": 0.0,
                    "feedback": f"カード{idx}に必須フィールドが不足しています",
                    "details": {},
                    "is_valid": False,
                    "card_index": idx,
                    "title": card.get("title", f"カード{idx}")
                }
                card_results.append(card_result)
                all_valid = False
                feedbacks.append(card_result["feedback"])
                continue
            # バリデーション
            is_valid_format, format_message, format_details = validate_structure_format(card)
            if not is_valid_format:
                logger.warning(f"⚠️ カード{idx}のバリデーションエラー: {format_message}")
                card_result = {
                    "score": 0.0,
                    "feedback": format_message,
                    "details": format_details,
                    "is_valid": False,
                    "card_index": idx,
                    "title": card.get("title", f"カード{idx}")
                }
                card_results.append(card_result)
                all_valid = False
                feedbacks.append(format_message)
                continue
            # Claude等で評価
            prompt = pm.get_prompt(provider, "structure_evaluation")
            formatted_prompt = prompt.format(structure=card)
            from src.llm import call_model as llm_call_model
            response = llm_call_model(
                model=get_model_for_provider(provider),
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=0.3,
                max_tokens=1000,
                provider=provider
            )
            evaluation_data = extract_json_part(response.get("content", ""))
            score = float(evaluation_data.get("score", 0.0))
            is_valid = bool(evaluation_data.get("is_valid", False))
            feedback = str(evaluation_data.get("feedback", ""))
            details = evaluation_data.get("details", {})
            card_result = {
                "score": score,
                "feedback": feedback,
                "details": details,
                "is_valid": is_valid,
                "card_index": idx,
                "title": card.get("title", f"カード{idx}")
            }
            card_results.append(card_result)
            total_score += score
            all_valid = all_valid and is_valid
            feedbacks.append(feedback)
        # 平均スコア
        avg_score = total_score / len(card_results) if card_results else 0.0
        # 全体の評価結果
        return {
            "is_valid": all_valid,
            "score": avg_score,
            "feedback": "\n".join(feedbacks),
            "details": {"card_results": card_results},
            "card_results": card_results
        }
    else:
        # 単一カード（dict）
        # 必須フィールドチェック
        if not structure.get("title") or not structure.get("content"):
            logger.warning("⚠️ evaluate_structure_with - 必須フィールド（title, content）が不足しています")
            return EvaluationResult(
                score=0.0,
                feedback="構成に必須フィールドが不足しているため、評価できませんでした。",
                details={},
                is_valid=False
            )
        # バリデーション
        is_valid_format, format_message, format_details = validate_structure_format(structure)
        if not is_valid_format:
            logger.warning(f"⚠️ evaluate_structure_with - 構成形式が不正: {format_message}")
            return EvaluationResult(
                score=0.0,
                feedback=format_message,
                details=format_details,
                is_valid=False
            )
        # Claude等で評価
        prompt = pm.get_prompt(provider, "structure_evaluation")
        formatted_prompt = prompt.format(structure=structure)
        from src.llm import call_model as llm_call_model
        response = llm_call_model(
            model=get_model_for_provider(provider),
            messages=[{"role": "user", "content": formatted_prompt}],
            temperature=0.3,
            max_tokens=1000,
            provider=provider
        )
        evaluation_data = extract_json_part(response.get("content", ""))
        score = float(evaluation_data.get("score", 0.0))
        is_valid = bool(evaluation_data.get("is_valid", False))
        feedback = str(evaluation_data.get("feedback", ""))
        details = evaluation_data.get("details", {})
        return EvaluationResult(
            score=score,
            feedback=feedback,
            details=details,
            is_valid=is_valid
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

def validate_structure_format(structure: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
    """
    構成データの形式妥当性をチェックするフィルタ
    
    Args:
        structure: チェック対象の構成データ（トップレベルにtitle, contentを持つdict）
    
    Returns:
        tuple[bool, str, Dict[str, Any]]: (妥当性, エラーメッセージ, 詳細情報)
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "field_checks": {}
    }
    
    # 必須フィールドのチェック
    required_fields = ["title", "content"]
    for field in required_fields:
        if field not in structure:
            validation_result["errors"].append(f"必須フィールド '{field}' が不足しています")
            validation_result["is_valid"] = False
        elif not structure[field]:
            validation_result["errors"].append(f"必須フィールド '{field}' が空です")
            validation_result["is_valid"] = False
        else:
            validation_result["field_checks"][field] = {
                "exists": True,
                "type": type(structure[field]).__name__,
                "length": len(str(structure[field])) if structure[field] else 0
            }
    
    # titleフィールドの詳細チェック
    if "title" in structure and structure["title"]:
        title = structure["title"]
        if not isinstance(title, str):
            validation_result["errors"].append("titleフィールドは文字列である必要があります")
            validation_result["is_valid"] = False
        elif len(title.strip()) < 3:
            validation_result["warnings"].append("titleフィールドが短すぎます（3文字以上推奨）")
    
    # contentフィールドの詳細チェック
    if "content" in structure and structure["content"]:
        content = structure["content"]
        if not isinstance(content, dict):
            validation_result["errors"].append("contentフィールドは辞書型である必要があります")
            validation_result["is_valid"] = False
        elif not content:
            validation_result["errors"].append("contentフィールドが空の辞書です")
            validation_result["is_valid"] = False
        else:
            # content内の項目数をチェック
            content_items = len(content)
            validation_result["field_checks"]["content_items"] = content_items
            if content_items < 1:
                validation_result["warnings"].append("contentフィールドに項目がありません")
    
    # descriptionフィールドのオプショナルチェック
    if "description" in structure:
        description = structure["description"]
        if description and not isinstance(description, str):
            validation_result["warnings"].append("descriptionフィールドは文字列であることを推奨します")
        validation_result["field_checks"]["description"] = {
            "exists": True,
            "type": type(description).__name__ if description else "None",
            "length": len(str(description)) if description else 0
        }
    
    # エラーメッセージの生成
    error_message = ""
    if validation_result["errors"]:
        error_message = "構成データの形式に問題があります: " + "; ".join(validation_result["errors"])
    elif validation_result["warnings"]:
        error_message = "構成データに警告があります: " + "; ".join(validation_result["warnings"])
    else:
        error_message = "構成データの形式は妥当です"
    
    return validation_result["is_valid"], error_message, validation_result 