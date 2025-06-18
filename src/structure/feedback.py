"""
フィードバックモジュール - 評価結果のUI処理
"""

import logging
from typing import Dict, Any, List, Optional
from src.types import EvaluationResult
from src.structure.evaluator import evaluate_structure_with
from src.llm.providers.claude import call_claude_evaluation, call_claude_api
from src.llm.providers.gemini import call_gemini_api
import difflib
import html

logger = logging.getLogger(__name__)

def process_evaluation_result(result: EvaluationResult) -> Dict[str, Any]:
    """
    評価結果をUI表示用に加工
    
    Args:
        result (EvaluationResult): 評価結果
        
    Returns:
        Dict[str, Any]: UI表示用の加工済み結果
    """
    # エラーがある場合はエラーメッセージを表示
    if result["error"]:
        return {
            "status": "error",
            "message": f"評価に失敗しました: {result['error']}",
            "details": None
        }
    
    # スコアに基づいて評価を判定
    intent_status = "good" if result["intent_match"] >= 0.8 else "warning" if result["intent_match"] >= 0.5 else "error"
    quality_status = "good" if result["quality_score"] >= 0.8 else "warning" if result["quality_score"] >= 0.5 else "error"
    
    return {
        "status": "success",
        "message": "評価が完了しました",
        "details": {
            "intent": {
                "score": result["intent_match"],
                "status": intent_status,
                "reason": result["intent_reason"]
            },
            "quality": {
                "score": result["quality_score"],
                "status": quality_status,
                "suggestions": result["improvement_suggestions"]
            }
        }
    }

def get_structure_feedback(content: Dict[str, Any]) -> Dict[str, Any]:
    """構造に対するフィードバックを取得する"""
    try:
        # 評価の実行
        result = evaluate_structure_with("claude", content)
        
        return {
            "score": result.score,
            "feedback": result.feedback,
            "details": result.details,
            "is_valid": result.is_valid
        }
    except Exception as e:
        return {
            "score": 0.0,
            "feedback": f"評価中にエラーが発生しました: {str(e)}",
            "details": {},
            "is_valid": False
        }

def analyze_structure_and_suggest(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    構成データを分析し、フィードバックと改善提案を提供する
    
    Args:
        structure (Dict[str, Any]): 分析対象の構成データ
        
    Returns:
        Dict[str, Any]: 分析結果
            - score (float): 0〜1の評価スコア
            - is_valid (bool): 有効性判定
            - suggestions (List[str]): 改善提案のリスト
    """
    try:
        # 評価用プロンプトの構築
        messages = [
            {
                "role": "user",
                "content": f"""以下の構成データを評価し、JSON形式で結果を返してください。
評価基準：
1. 構造の一貫性（0.0-1.0）
2. 内容の充実度（0.0-1.0）
3. 改善提案（具体的な提案をリスト形式で）

構成データ：
{json.dumps(structure, ensure_ascii=False, indent=2)}

以下のJSON形式で返してください：
{{
    "score": 0.0-1.0の数値,
    "suggestions": ["改善提案1", "改善提案2", ...]
}}"""
            }
        ]
        
        # Claude APIを呼び出して評価
        result = call_claude_evaluation(messages)
        
        # 結果のバリデーション
        if not result or not isinstance(result, dict):
            logger.warning("Invalid evaluation result format")
            return {
                "score": 0.0,
                "is_valid": False,
                "suggestions": []
            }
        
        # スコアの取得と正規化
        score = float(result.get("score", 0.0))
        score = max(0.0, min(1.0, score))  # 0.0-1.0の範囲に収める
        
        # 改善提案の取得
        suggestions = result.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []
        
        # 有効性の判定（スコアが0.6以上を有効とする）
        is_valid = score >= 0.6
        
        return {
            "score": score,
            "is_valid": is_valid,
            "suggestions": suggestions
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse structure data: {str(e)}")
        return {
            "score": 0.0,
            "is_valid": False,
            "suggestions": []
        }
    except Exception as e:
        logger.error(f"Error in structure analysis: {str(e)}")
        return {
            "score": 0.0,
            "is_valid": False,
            "suggestions": []
        }

def call_gemini_ui_generator(structure: Dict[str, Any]) -> str:
    """
    Gemini APIを使用してUI提案を生成する
    
    Args:
        structure (Dict[str, Any]): 構成データ
        
    Returns:
        str: UI提案のテキスト
             エラー時は空文字列を返す
    """
    try:
        # プロンプトの構築
        messages = [
            {
                "role": "user",
                "content": f"""以下の構成データに基づいて、UIの設計提案を生成してください。
提案には以下の要素を含めてください：
1. 画面レイアウトの概要
2. 主要なUIコンポーネントの配置
3. ユーザーフロー
4. インタラクションの提案

構成データ：
{json.dumps(structure, ensure_ascii=False, indent=2)}

提案は具体的で実装可能な形で記述してください。"""
            }
        ]
        
        # Gemini APIを呼び出し
        response = call_gemini_api(messages)
        
        if not response:
            logger.warning("Empty response from Gemini API")
            return ""
            
        return response
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse structure data: {str(e)}")
        return ""
    except Exception as e:
        logger.warning(f"Error in UI generation: {str(e)}")
        return ""

def get_diff_highlighted(new_text: str, old_text: str) -> str:
    """
    新旧テキストの差分をHTMLで強調表示する
    
    Args:
        new_text (str): 新しいテキスト
        old_text (str): 古いテキスト
        
    Returns:
        str: 差分を強調表示したHTML
             エラー時は空文字列を返す
    """
    try:
        # テキストを行に分割
        new_lines = new_text.splitlines()
        old_lines = old_text.splitlines()
        
        # 差分を計算
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        result = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # 変更なしの行はそのまま
                result.extend(new_lines[j1:j2])
            elif tag == 'replace':
                # 置換された行は両方表示
                result.extend([f'<span class="diff-del">{html.escape(line)}</span>' for line in old_lines[i1:i2]])
                result.extend([f'<span class="diff-add">{html.escape(line)}</span>' for line in new_lines[j1:j2]])
            elif tag == 'delete':
                # 削除された行
                result.extend([f'<span class="diff-del">{html.escape(line)}</span>' for line in old_lines[i1:i2]])
            elif tag == 'insert':
                # 追加された行
                result.extend([f'<span class="diff-add">{html.escape(line)}</span>' for line in new_lines[j1:j2]])
        
        # 結果を結合
        return '<br>'.join(result)
        
    except Exception as e:
        logger.warning(f"Error in diff generation: {str(e)}")
        return ""

def call_claude(structure: Dict[str, Any]) -> str:
    """
    Claudeを使って構成を整形する基本関数
    
    Args:
        structure (Dict[str, Any]): 整形対象の構成データ
        
    Returns:
        str: 整形された構成データ
             エラー時は空文字列を返す
    """
    prompt = f"次の構成を改善・整形してください：\n{json.dumps(structure, ensure_ascii=False)}"
    try:
        result = call_claude_api(prompt, model="claude-3-opus-20240229", temperature=0.2)
        return result or ""
    except Exception as e:
        logger.warning(f"[call_claude] Claude呼び出しエラー: {e}")
        return ""

def call_claude_and_gpt(structure: Dict[str, Any]) -> Dict[str, str]:
    """
    ClaudeとGPTを組み合わせて構成を分析・整形する関数（予備処理用）
    
    Args:
        structure (Dict[str, Any]): 分析対象の構成データ
        
    Returns:
        Dict[str, str]: 分析結果
            - claude (str): Claudeの出力
            - gpt (str): GPTの出力
    """
    claude_result = call_claude(structure)
    if not claude_result:
        return {"claude": "", "gpt": ""}

    # Claude結果をChatGPTに再評価させるなどの連携が想定される
    try:
        from src.llm.providers.chatgpt import call_chatgpt_api
        prompt = f"次のClaude出力をもとに、構成として完成させてください：\n{claude_result}"
        gpt_result = call_chatgpt_api(prompt, model="gpt-4", temperature=0.2)
        return {"claude": claude_result, "gpt": gpt_result or ""}
    except Exception as e:
        logger.warning(f"[call_claude_and_gpt] GPT呼び出しエラー: {e}")
        return {"claude": claude_result, "gpt": ""}

__all__ = [
    'analyze_structure_and_suggest',
    'call_gemini_ui_generator',
    'get_diff_highlighted',
    'call_claude',
    'call_claude_and_gpt'
]