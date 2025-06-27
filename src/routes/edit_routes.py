"""
編集ルートモジュール
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional, List
from src.structure.evaluator import evaluate_structure
from src.exceptions import AIProviderError
import logging
from src.structure.utils import save_structure, load_structure
from src.structure.evaluator import evaluate_structure_with
from src.structure.diff_utils import generate_diff_html
from src.types import EvaluationResult
from src.common.logging_utils import get_logger

logger = get_logger("root")

edit_bp = Blueprint('edit', __name__)

@edit_bp.route('/evaluate', methods=['POST'])
def evaluate_structure_endpoint():
    """
    構造を評価するエンドポイント
    """
    try:
        content = request.get_json()
        if not content:
            return jsonify({
                "status": "error",
                "message": "リクエストボディが空です"
            }), 400
        # contentを文字列化して渡す（例: JSON文字列化）
        structure_str = str(content) if isinstance(content, str) else str(content)
        structure_dict = content if isinstance(content, dict) else {}
        result = evaluate_structure_with(structure_dict) or {}
        return jsonify({
            "status": "success",
            "result": {
                "score": result.get("score"),
                "feedback": result.get("feedback"),
                "details": result.get("details"),
                "is_valid": result.get("is_valid")
            }
        })
    except AIProviderError as e:
        logger.error(f"AI評価エラー: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"AI評価に失敗しました: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"予期せぬエラー: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"予期せぬエラーが発生しました: {str(e)}"
        }), 500

@edit_bp.route('/ajax_save/<structure_id>', methods=['POST'])
def ajax_save_structure(structure_id):
    """Ajaxで構造を保存し、Claude評価を即座に実行。失敗時はGemini補完と差分表示"""
    logger.info(f"💾 構造保存開始 - structure_id: {structure_id}")
    
    try:
        data = request.get_json()
        if not data:
            logger.warning(f"❌ 保存データが空です - structure_id: {structure_id}")
            return jsonify({"success": False, "error": "データがありません"}), 400
        
        # 構造情報をログに出力
        title = data.get("title", "タイトルなし")
        logger.info(f"📋 保存対象構造 - ID: {structure_id}, タイトル: {title}")
        
        # 構造の保存
        save_structure(structure_id, data)
        logger.info(f"✅ 構造保存成功 - structure_id: {structure_id}, タイトル: {title}")
        
        # 元の構成内容を保存（差分比較用）
        original_content = data.get("content", {})
        
        # Claude評価を実行
        claude_result = None
        claude_evaluation = None
        try:
            logger.info(f"🔍 Claude評価開始 - structure_id: {structure_id}")
            claude_result = evaluate_structure_with(data, "claude")
            claude_evaluation = f"<pre>{str(claude_result)}</pre>"
            logger.info(f"✅ Claude評価完了 - structure_id: {structure_id}")
            
            # Claudeが成功した場合は差分なしで返す
            return jsonify({
                "success": True,
                "evaluation": claude_evaluation,
                "diff_html": None
            })
            
        except Exception as claude_error:
            logger.warning(f"⚠️ Claude評価失敗 - structure_id: {structure_id}, error: {str(claude_error)}")
            
            # Claude失敗時はGemini補完を実行
            try:
                logger.info(f"🔄 Gemini補完評価開始 - structure_id: {structure_id}")
                gemini_result = evaluate_structure_with(data, "gemini")
                gemini_evaluation = f"<pre>{str(gemini_result)}</pre>"
                logger.info(f"✅ Gemini補完評価完了 - structure_id: {structure_id}")
                
                # Geminiの結果から新しい構成内容を取得
                gemini_content = {}
                if hasattr(gemini_result, 'content'):
                    gemini_content = gemini_result.content
                elif isinstance(gemini_result, dict):
                    gemini_content = gemini_result.get('content', {})
                
                # 差分HTMLを生成
                diff_html = generate_diff_html(original_content, gemini_content)
                
                return jsonify({
                    "success": True,
                    "evaluation": gemini_evaluation,
                    "diff_html": diff_html
                })
                
            except Exception as gemini_error:
                logger.error(f"❌ Gemini補完評価も失敗 - structure_id: {structure_id}, error: {str(gemini_error)}")
                return jsonify({
                    "success": False,
                    "error": f"Claude評価とGemini補完評価の両方に失敗しました。Claude: {str(claude_error)}, Gemini: {str(gemini_error)}"
                }), 500
            
    except Exception as e:
        logger.exception(f"❌ 構造保存中にエラーが発生 - structure_id: {structure_id}, error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500 