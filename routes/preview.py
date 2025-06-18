from flask import Blueprint, render_template, flash, redirect, url_for, request
from src.structure.utils import load_structure_by_id
from src.structure.validator import evaluate_structure_content
from src.structure.preview import render_html_from_structure  # ← 追加
import json
import logging

logger = logging.getLogger(__name__)

preview_bp = Blueprint('preview', __name__, url_prefix='/preview')

@preview_bp.route('/<structure_id>')
def preview_structure(structure_id):
    structure = load_structure_by_id(structure_id)

    try:
        content = structure["content"]
        if isinstance(content, str):
            content = json.loads(content)

        # ✅ 追加：セクション・ページを明示的に渡す
        structure["sections"] = content.get("sections", [])
        structure["pages"] = content.get("pages", [])  # ← ここを追加

        # ✅ 自動生成プレビュー（HTMLとして描画）
        rendered_html = render_html_from_structure(content)

    except Exception as e:
        logger.warning(f"[Preview] JSON読み込みエラー: {e}")
        structure["sections"] = []
        structure["pages"] = []
        rendered_html = "<p style='color:red;'>⚠️ 内容の解析に失敗しました。</p>"

    return render_template(
        'structure_preview.html',
        structure=structure,
        rendered_html=rendered_html
    )

@preview_bp.route('/submit/<structure_id>', methods=['POST'])
def submit_structure(structure_id):
    submitted_data = request.form.to_dict(flat=False)

    # ✅ コンソールに入力データを出力（テスト確認用）
    print(f"[PREVIEW SUBMIT] {structure_id} 入力: {submitted_data}", flush=True)

    formatted = "\n".join([f"{k}: {', '.join(v)}" for k, v in submitted_data.items()])
    flash(f"📨 フォームが送信されました。\n\n{formatted}", "success")

    return redirect(url_for('preview.preview_structure', structure_id=structure_id))
