from typing import Dict, Any, List, Optional
from src.types import StructureDict, EvaluationResult

CURSOR_SYSTEM_PROMPT = """
あなたは構成テンプレートを評価するAIです。
以下の構成に対して、以下の観点で評価を行ってください：

1. 意図一致度（0-100点）
2. 品質スコア（0-100点）
3. 評価理由
4. 改善提案

評価結果は以下のJSON形式で返してください：

{
    "score": 85.5,
    "comment": "全体的に良い構成ですが、いくつかの改善点があります",
    "intent_match": 90,
    "quality_score": 85,
    "intent_reason": "ユーザーの意図をよく理解し、適切な構成になっています"
}
"""

CURSOR_STRUCTURE_GENERATION_PROMPT = """
あなたは構成テンプレートを生成するAIです。
以下の要件に基づいて、構成テンプレートを生成してください：

1. タイトル
2. 説明
3. コンテンツ（セクションごとの詳細）

生成結果は以下のJSON形式で返してください：

{
    "title": "タイトル",
    "description": "説明",
    "content": {
        "セクション1": {
            "項目1": "内容1",
            "項目2": "内容2"
        },
        "セクション2": {
            "項目1": "内容1",
            "項目2": "内容2"
        }
    }
}
"""

def format_evaluation_prompt(structure: StructureDict) -> str:
    """
    評価用のプロンプトをフォーマットする
    
    Args:
        structure (StructureDict): 評価対象の構成
        
    Returns:
        str: フォーマットされたプロンプト
    """
    return f"""
以下の構成を評価してください：

タイトル: {structure.get('title', '')}
説明: {structure.get('description', '')}
コンテンツ: {structure.get('content', {})}
"""

def format_generation_prompt(requirements: str) -> str:
    """
    生成用のプロンプトをフォーマットする
    
    Args:
        requirements (str): 要件
        
    Returns:
        str: フォーマットされたプロンプト
    """
    return f"""
以下の要件に基づいて構成テンプレートを生成してください：

{requirements}
""" 