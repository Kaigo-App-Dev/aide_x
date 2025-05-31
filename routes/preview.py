from flask import Blueprint, render_template, flash, redirect, url_for, request
from utils.structure_utils import load_structure_by_id
from utils.structure_validator import evaluate_structure_content
import json
import logging

logger = logging.getLogger(__name__)

preview_bp = Blueprint('preview', __name__, url_prefix='/preview')

@preview_bp.route('/<structure_id>')
def preview_structure(structure_id):
    structure = load_structure_by_id(structure_id)

    # ✅ プレビュー表示に必要な構成パース処理を追加（Step 16-2対応）
    try:
        content = json.loads(structure["content"])
        structure["sections"] = content.get("sections", [])
    except Exception as e:
        logger.warning(f"[Preview] JSON読み込みエラー: {e}")
        structure["sections"] = []

    return render_template('structure_preview.html', structure=structure)

@preview_bp.route('/submit/<structure_id>', methods=['POST'])
def submit_structure(structure_id):
    submitted_data = request.form.to_dict(flat=False)

    # ✅ コンソールに入力データを出力（テスト確認用）
    print(f"[PREVIEW SUBMIT] {structure_id} 入力: {submitted_data}", flush=True)

    formatted = "\n".join([f"{k}: {', '.join(v)}" for k, v in submitted_data.items()])
    flash(f"📨 フォームが送信されました。\n\n{formatted}", "success")

    return redirect(url_for('preview.preview_structure', structure_id=structure_id))
