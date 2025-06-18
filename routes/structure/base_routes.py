from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app, session
from flask_login import login_required, current_user
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from src.llm.gemini_utils import call_gemini_ui
from src.llm.providers.gemini import call_gemini_api

from src.structure.validator import (
    evaluate_structure_content,
    validate_structure
)

from src.structure.feedback import (
    analyze_structure_and_suggest,
    call_gemini_ui_generator,
    get_diff_highlighted as get_diff_highlighted_feedback
)

from src.structure.utils import (
    get_structure,
    save_structure,
    get_candidates_for_evolution,
    update_structure_content,
    get_structure_path,
    get_history_path,
    load_structures,
    load_structure_by_id,
    load_previous_version,
    append_structure_log,
    summarize_structure,
    summarize_user_requirements,
    normalize_structure_for_pages,
    ensure_json_string,
    normalize_structure_format
)

from src.llm.claude import call_claude_evaluation
from src.structure.feedback import call_claude, call_claude_and_gpt

from src.structure.ui_generator import (
    generate_ui_with_gemini,
    call_gemini_ui_generator
)

from src.common.preview import render_html_from_structure
from src.common.diff import get_diff_highlighted

from src.structure.evaluation import evaluate_with_claude

# ロガーの設定
logger = logging.getLogger(__name__)

# Blueprintはinitからインポート
from . import structure_bp

print("[OK] base_routes.py 読み込まれました")

@structure_bp.route('/')
def index():
    return render_template('structure/index.html')

@structure_bp.route('/generate', methods=['POST'])
def generate_structure():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'error': 'プロンプトが空です'}), 400
            
        # Gemini APIを呼び出して構造を生成
        structure = call_gemini_ui(prompt)
        
        return jsonify({'structure': structure})
        
    except Exception as e:
        logger.error(f"構造生成中にエラーが発生: {str(e)}")
        return jsonify({'error': '構造の生成中にエラーが発生しました'}), 500

@structure_bp.route('/list')
def list_structures():
    try:
        logger.info("📥 list_structures に入りました")
        structures = load_structures()
        logger.info(f"📦 構成数: {len(structures)} 件")
        return render_template('structure_list.html', structures=structures)
    except Exception as e:
        logger.error(f"❌ list_structures で例外: {e}")
        return f"❌ 構成リスト取得エラー: {e}", 500

@structure_bp.route('/new', methods=['GET', 'POST'])
def new_structure():
    if request.method == 'POST':
        new_id = str(uuid4())
        new_structure = {
            "id": new_id,
            "title": request.form.get('title', ''),
            "description": request.form.get('description', ''),
            "content": request.form.get('content', ''),
            "is_final": False
        }
        errors = validate_structure(new_structure)
        if errors:
            return render_template('edit_structure.html', structure=new_structure, errors=errors)
        save_structure(new_id, new_structure)
        return redirect(url_for('structure.edit_structure', structure_id=new_id))

    empty_structure = {
        "id": "",
        "title": "",
        "description": "",
        "content": "",
        "is_final": False
    }
    return render_template('edit_structure.html', structure=empty_structure)

@structure_bp.route("/edit/<structure_id>", methods=["GET", "POST"])
def edit_structure(structure_id):
    try:
        structure = load_structure_by_id(structure_id)
        if not structure:
            logger.error(f"❌ Structure not found: {structure_id}")
            return "404 Structure not found", 404

        # contentフィールドの安全な取得と検証
        content_str = structure.get("content")
        if not content_str:
            logger.warning(f"⚠ Content is empty for structure: {structure_id}")
            content = {"sections": [], "pages": []}
        else:
            try:
                # contentが既にdictの場合はそのまま使用
                if isinstance(content_str, dict):
                    content = content_str
                else:
                    # 文字列の場合はJSONとしてパース
                    content = json.loads(content_str)
            except json.JSONDecodeError as e:
                logger.error(f"⚠ Invalid JSON in content for structure {structure_id}: {e}")
                content = {"sections": [], "pages": []}

        # 安全にセクションとページを取得
        structure["sections"] = content.get("sections", [])
        structure["pages"] = content.get("pages", [])

        return render_template(
            "edit_structure.html",
            structure=structure,
            evaluation={},
            diff_html="",
            gemini_output="",
            logs=[]
        )
    except Exception as e:
        logger.error(f"❌ edit_structure()内でエラー: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return "500 Internal Server Error", 500

@structure_bp.route("/gemini_generate_ui/<structure_id>", methods=["POST"], endpoint="gemini_generate_ui_from_button")
def gemini_generate_ui_from_button(structure_id):
    try:
        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({
                'success': False,
                'message': '構造が見つかりません'
            }), 404

        # コンテンツの取得と検証
        content = structure.get('content')
        if not content:
            return jsonify({
                'success': False,
                'message': 'コンテンツが空です'
            }), 400

        # Gemini APIを呼び出してUIを生成
        ui_pages = call_gemini_ui_generator(content)
        
        return jsonify({
            'success': True,
            'ui_pages': ui_pages
        })
        
    except Exception as e:
        logger.error(f"UI生成中にエラーが発生: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'UIの生成中にエラーが発生しました'
        }), 500

@structure_bp.route("/export/<structure_id>")
def export_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "404 Structure not found", 404
    return jsonify(structure)

@structure_bp.route("/export/start/<structure_id>", methods=["POST"])
def start_export(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "404 Structure not found", 404
    return jsonify({"status": "success"})

@structure_bp.route("/repair/<structure_id>", methods=["POST"])
def repair_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "404 Structure not found", 404

    evaluation = call_claude(structure.get("content", ""))
    logs = structure.get("logs", [])

    return render_template('edit_structure.html',
                           structure=structure,
                           evaluation=evaluation,
                           logs=logs,
                           errors=[])

@structure_bp.route("/evaluate/<structure_id>")
def evaluate_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "404 Structure not found", 404
    return jsonify({"status": "success"})

@structure_bp.route("/improve/<structure_id>")
def improve_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "404 Structure not found", 404
    return jsonify({"status": "success"})

@structure_bp.route("/delete/<structure_id>", methods=["POST"])
def delete_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "404 Structure not found", 404

    path = get_structure_path(structure_id)
    if os.path.exists(path):
        os.remove(path)
        flash("構成を削除しました", "success")
    else:
        flash("構成ファイルが見つかりません", "error")

    return redirect(url_for('structure.list_structures'))

@structure_bp.route("/ajax_save/<structure_id>", methods=["POST"])
def ajax_save_structure(structure_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "データが空です"}), 400

        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({"error": "構成が見つかりません"}), 404

        # 更新
        structure.update(data)
        save_structure(structure_id, structure)

        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"保存中にエラーが発生: {str(e)}")
        return jsonify({"error": "保存中にエラーが発生しました"}), 500

@structure_bp.route("/structure/evaluate", methods=["POST"])
def evaluate_structure_post():
    logger.info("🧪 /structure/evaluate エンドポイントにアクセスされました")
    """
    構造体の評価を行う
    
    Returns:
        Response: JSONレスポンス
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "リクエストデータがありません"}), 400

        # 構造体の正規化
        structure = normalize_structure_format(data)
        
        # 構造体の検証
        is_valid, errors = validate_structure(structure)
        if not is_valid:
            return jsonify({
                "error": "構造体の検証に失敗しました",
                "details": errors
            }), 400

        # Claudeによる評価
        evaluation_result = evaluate_with_claude(structure)
        
        # 評価結果の保存
        session["evaluation_result"] = evaluation_result
        session.modified = True

        return jsonify({
            "success": True,
            "evaluation": evaluation_result
        })

    except Exception as e:
        logger.exception("構造体の評価中にエラーが発生しました")
        return jsonify({"error": str(e)}), 500


