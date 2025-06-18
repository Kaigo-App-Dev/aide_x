"""
Common Types and Utilities

このモジュールは、評価機能で共有される型とユーティリティを提供します。
"""

from typing import TypedDict, Dict, Any

class EvaluationResult(TypedDict):
    """評価結果の型定義"""
    score: float
    feedback: str
    details: Dict[str, Any]
    is_valid: bool 