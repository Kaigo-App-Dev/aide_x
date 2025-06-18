"""
編集ルートモジュール
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional
from src.structure.evaluator import evaluate_structure
from src.common.exceptions import AIProviderError
import logging
from src.structure.utils import save_structure, load_structure
from src.structure.evaluator import evaluate_structure_with
from src.common.types import EvaluationResult

logger = logging.getLogger(__name__)

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
        result = evaluate_structure(structure_str)
        return jsonify({
            "status": "success",
            "result": {
                "score": result.score,
                "feedback": result.feedback,
                "details": result.details,
                "is_valid": result.is_valid
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
    """Ajaxで構造を保存する"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "データがありません"}), 400
        # 構造の保存
        save_structure(structure_id, data)
        # dataを文字列化して評価
        structure_str = str(data) if isinstance(data, str) else str(data)
        result = evaluate_structure(structure_str)
        return jsonify({
            "success": True,
            "evaluation": {
                "score": result.score,
                "feedback": result.feedback,
                "details": result.details,
                "is_valid": result.is_valid
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500 