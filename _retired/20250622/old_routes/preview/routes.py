from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

from src.structure.utils import load_structure_by_id

preview_bp = Blueprint('preview', __name__)

@preview_bp.route('/')
def index():
    return render_template('preview/index.html')

@preview_bp.route('/<structure_id>', methods=['GET'], endpoint='preview_structure')
def preview_structure(structure_id):
    try:
        structure = load_structure_by_id(structure_id)
        if not structure:
            return "構成が見つかりません", 404
        return render_template('preview/preview.html', structure=structure)
    except Exception as e:
        return f"プレビュー表示中にエラーが発生しました: {str(e)}", 500

@preview_bp.route('/generate', methods=['POST'])
def generate_preview():
    try:
        data = request.get_json()
        structure = data.get('structure', '')
        
        if not structure:
            return jsonify({'error': '構造が空です'}), 400
            
        # TODO: プレビュー生成の実装
        return jsonify({'preview': 'プレビューの内容'})
        
    except Exception as e:
        return jsonify({'error': 'プレビューの生成中にエラーが発生しました'}), 500 