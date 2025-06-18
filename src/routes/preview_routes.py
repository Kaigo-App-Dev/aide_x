"""
プレビュールート定義モジュール
"""

from flask import Blueprint, request, jsonify
from src.llm.controller import AIController

preview_bp = Blueprint('preview', __name__, url_prefix='/preview')

@preview_bp.route('/new', methods=['POST'])
def new_preview():
    """新しいプレビューの作成"""
    try:
        data = request.get_json()
        if not data or 'user_input' not in data:
            return jsonify({
                'error': 'Invalid request data',
                'message': 'user_input is required'
            }), 400
        
        # TODO: AIコントローラーを使用してプレビューを生成
        return jsonify({
            'status': 'ok',
            'message': 'Preview created successfully'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to create preview'
        }), 500 