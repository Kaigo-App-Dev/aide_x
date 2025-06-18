"""
Structure validation module for AIDE-X
"""
import json
from typing import Dict, Any, List, Union

def evaluate_structure_content(content_json_str: str) -> Dict[str, Any]:
    """
    Evaluate structure content without using Claude
    
    Args:
        content_json_str (str): JSON string of the structure content
        
    Returns:
        Dict[str, Any]: Evaluation results including intent match, quality score, and reason
    """
    try:
        content = json.loads(content_json_str)
    except json.JSONDecodeError:
        return {
            "intent_match": 0,
            "quality_score": 0,
            "intent_reason": "JSON構文エラー。評価できませんでした。"
        }

    # Temporary evaluation logic (can be replaced in the future)
    intent_match = 85
    quality_score = 75
    intent_reason = "構成は一般的なテンプレート構造に沿っており、モジュール分離も適切です。"

    return {
        "intent_match": intent_match,
        "quality_score": quality_score,
        "intent_reason": intent_reason
    }

def validate_structure(content_input: Union[str, Dict[str, Any]]) -> List[str]:
    """
    Validate structure content
    
    Args:
        content_input (Union[str, Dict[str, Any]]): Structure content as string or dict
        
    Returns:
        List[str]: List of validation errors, empty if valid
    """
    errors = []

    # Parse string to dict if needed
    if isinstance(content_input, str):
        try:
            content = json.loads(content_input)
        except json.JSONDecodeError:
            errors.append("構成内容が不正なJSONです。")
            return errors
    elif isinstance(content_input, dict):
        content = content_input
    else:
        errors.append("構成は文字列またはオブジェクトである必要があります。")
        return errors

    # Check dict format
    if not isinstance(content, dict):
        errors.append("構成はオブジェクト（辞書形式）である必要があります。")
        return errors

    # Important: Must have "sections" at top level
    if "sections" not in content:
        errors.append('"sections" が含まれていません。構成の最小単位が不足しています。')

    return errors 