"""
ベースルート定義モジュール
"""

from flask import Blueprint, jsonify

base_bp = Blueprint('base', __name__)

@base_bp.route('/')
def index():
    """トップページ"""
    return jsonify({
        'status': 'ok',
        'message': 'AIDE-X API is running'
    })

@base_bp.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'ok',
        'message': 'Service is healthy'
    }) 