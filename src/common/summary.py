from typing import List, Dict, Any, Optional
from src.common.types import StructureDict, EvaluationResult

def summarize_user_requirements(chat_history: List[Dict[str, Any]]) -> str:
    """
    ユーザーのチャット履歴から要件を要約する（簡易版）
    
    Args:
        chat_history (List[Dict[str, Any]]): チャット履歴
        
    Returns:
        str: 要約された要件
    """
    # ユーザーの発話だけを抜き出してまとめる
    user_inputs = [msg["content"] for msg in chat_history if msg["role"] == "user"]
    summary = "・" + "\n・".join(user_inputs[-5:])  # 最新5件だけ例として表示
    return summary 

def summarize_structure(structure: StructureDict) -> str:
    """
    構成の要約を生成する
    
    Args:
        structure (StructureDict): 要約対象の構成
        
    Returns:
        str: 要約テキスト
    """
    summary_parts = []
    
    # タイトルの要約
    if structure.get("title"):
        summary_parts.append(f"タイトル: {structure['title']}")
    
    # 説明の要約
    if structure.get("description"):
        summary_parts.append(f"説明: {structure['description']}")
    
    # コンテンツの要約
    content = structure.get("content", {})
    if content:
        summary_parts.append("コンテンツ:")
        for key, value in content.items():
            if isinstance(value, dict):
                items = [f"- {k}: {v}" for k, v in value.items()]
                summary_parts.append(f"  {key}:")
                summary_parts.extend(items)
            else:
                summary_parts.append(f"  {key}: {value}")
    
    return "\n".join(summary_parts)

def get_evaluation_summary(evaluation: EvaluationResult) -> str:
    """
    評価結果の要約を生成する
    
    Args:
        evaluation (EvaluationResult): 評価結果
        
    Returns:
        str: 要約テキスト
    """
    summary_parts = []
    
    # スコアの要約
    summary_parts.append(f"スコア: {evaluation['score']:.1f}")
    
    # コメントの要約
    if evaluation.get("comment"):
        summary_parts.append(f"コメント: {evaluation['comment']}")
    
    # メトリクスの要約
    if evaluation.get("metrics"):
        summary_parts.append("メトリクス:")
        for key, value in evaluation["metrics"].items():
            summary_parts.append(f"  {key}: {value}")
    
    return "\n".join(summary_parts) 