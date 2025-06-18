"""
Gemini Evaluator

このモジュールは、Geminiを使用した構造評価機能を提供します。
"""

from typing import Dict, Any
from src.structure.evaluator import evaluate_structure_with
from .common import EvaluationResult

class GeminiEvaluator:
    def evaluate(self, structure: Dict[str, Any]) -> EvaluationResult:
        return evaluate_structure_with("gemini", structure) 