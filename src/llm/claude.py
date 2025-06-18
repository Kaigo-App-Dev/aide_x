"""
Claude API integration module
"""

import logging
from typing import Dict, Any, List, Optional
from .providers.base import ChatMessage
from .prompts import prompt_manager, PromptManager
from src.exceptions import APIRequestError, ResponseFormatError

logger = logging.getLogger(__name__)

def call_claude_api(
    messages: List[ChatMessage],
    model: str = "claude-3-opus-20240229",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Claude APIを呼び出して応答を取得
    
    Args:
        messages: チャットメッセージのリスト
        model: 使用するモデル名
        temperature: 生成の多様性を制御するパラメータ（0.0-1.0）
        max_tokens: 生成する最大トークン数
        
    Returns:
        Dict[str, Any]: APIの応答
        
    Raises:
        APIRequestError: APIリクエストに失敗した場合
        ResponseFormatError: 応答の形式が不正な場合
    """
    try:
        # TODO: 実際のClaude API呼び出しを実装
        # 現在はスタブ実装
        logger.info(f"Calling Claude API with model: {model}")
        
        # 仮の応答を返す
        return {
            "content": "This is a stub response from Claude API.",
            "model": model,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error calling Claude API: {str(e)}")
        raise APIRequestError(f"Failed to call Claude API: {str(e)}")

def call_claude(
    prompt: str,
    model: str = "claude-3-opus-20240229",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """
    Claude APIを呼び出して応答を取得（簡易版）
    
    Args:
        prompt: プロンプト
        model: 使用するモデル名
        temperature: 生成の多様性を制御するパラメータ（0.0-1.0）
        max_tokens: 生成する最大トークン数
        
    Returns:
        str: 生成された応答
        
    Raises:
        APIRequestError: APIリクエストに失敗した場合
        ResponseFormatError: 応答の形式が不正な場合
    """
    try:
        messages = [
            ChatMessage(role="user", content=prompt)
        ]
        
        response = call_claude_api(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.get("content", "")
        
    except Exception as e:
        logger.error(f"Error in call_claude: {str(e)}")
        raise

def call_claude_evaluation(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Claudeで構成を評価する関数（スタブ版）
    
    Args:
        structure (Dict[str, Any]): 評価対象の構成データ
        
    Returns:
        Dict[str, Any]: Claudeからの評価レスポンス
        
    Raises:
        APIRequestError: APIリクエストに失敗した場合
        ResponseFormatError: 応答の形式が不正な場合
    """
    try:
        # プロンプトマネージャーから評価用プロンプトを取得
        prompt_manager.register_builtin_templates()
        evaluation_template = prompt_manager.get_prompt("claude", "evaluation_template")
        if not evaluation_template:
            raise ValueError("Evaluation template not found for Claude")
        
        # プロンプトをレンダリング
        prompt = evaluation_template.render(
            title=structure.get("title", ""),
            description=structure.get("description", ""),
            content=structure.get("content", {})
        )
        
        # メッセージを作成
        messages = [
            ChatMessage(role="user", content=prompt)
        ]
        
        # APIを呼び出し
        response = call_claude_api(
            messages=messages,
            model="claude-3-opus-20240229",
            temperature=0.3  # 評価では低めの温度を使用
        )
        
        # スタブ実装として、仮の評価結果を返す
        return {
            "score": 0.85,
            "feedback": "構成は全体的に良好です。以下の点が特に優れています：\n"
                       "1. 明確な構造と階層\n"
                       "2. 適切な命名規則の使用\n"
                       "3. 適切なコメントとドキュメント\n\n"
                       "改善の余地がある点：\n"
                       "1. 一部の関数の責務が大きすぎる可能性\n"
                       "2. エラーハンドリングの強化\n"
                       "3. テストカバレッジの向上",
            "details": {
                "structure_score": 0.9,
                "naming_score": 0.85,
                "documentation_score": 0.8,
                "complexity_score": 0.75
            },
            "model": "claude-3-opus-20240229",
            "timestamp": "2024-03-14T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error in call_claude_evaluation: {str(e)}")
        raise APIRequestError(f"Failed to evaluate structure: {str(e)}") 