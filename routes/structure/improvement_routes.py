"""
Improvement routes for structure management
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from . import structure_bp
from src.structure.utils import (
    load_structure_by_id, save_structure,
    append_structure_log, get_structure_path
)
from src.llm.providers.openai import generate_improvement
from uuid import uuid4
import os
from src.common.diff import get_diff_highlighted
from src.structure.evaluation import call_claude_and_gpt
from src.structure.utils import (
    get_structure,
    get_candidates_for_evolution
)
from typing import Dict, Any, Optional
import logging
from src.common.exceptions import APIRequestError, ResponseFormatError
from src.common.types import StructureDict, EvaluationResult
from src.structure.utils import (
    validate_structure,
    normalize_structure_format,
    load_structure
)

logger = logging.getLogger(__name__)

@structure_bp.route('/improve/<structure_id>')
def improve_structure(structure_id):
    structure = load_structure_by_id(structure_id)

    # ✅ ChatGPTに改善案を生成させる
    improved = generate_improvement(structure)

    # 改善案として仮保存
    improved_id = improved["id"]
    improved["from"] = structure_id
    improved["generated_by"] = "ChatGPT改善提案"

    save_structure(improved_id, improved)

    return redirect(url_for('chat.compare') + f"?original={structure_id}&modified={improved_id}")

@structure_bp.route('/adopt/<improved_id>/<original_id>', methods=['POST'])
def adopt_structure(improved_id, original_id):
    improved = load_structure_by_id(improved_id)
    original = load_structure_by_id(original_id)

    original["content"] = improved["content"]
    original["title"] = improved["title"] + "（採用）"
    original["generated_by"] = "ChatGPT改善採用"

    append_structure_log(original, "adopt", f"構成 {improved_id} を採用")

    save_structure(original_id, original)
    return redirect(url_for('structure.edit_structure', structure_id=original_id))

@structure_bp.route("/apply_repair/<structure_id>", methods=["POST"])
def apply_repair(structure_id):
    repaired = session.get("repaired_structure")
    if repaired:
        update_structure_content(structure_id, repaired)
        flash("修正構成を適用しました ✅", "success")
    else:
        flash("修正構成が見つかりません ❌", "danger")
    return redirect(url_for("structure.edit_structure", key=structure_id))

@structure_bp.route('/discard/<improved_id>', methods=['POST'])
def discard_structure(improved_id):
    path = get_structure_path(improved_id)

    if os.path.exists(path):
        structure = load_structure_by_id(improved_id)
        append_structure_log(structure, "discard", "改善案を不採用にした")
        save_structure(improved_id, structure)
        os.remove(path)

    return redirect(url_for('structure.list_structures'))


@structure_bp.route('/save_as_new/<improved_id>', methods=['POST'])
def save_as_new_structure(improved_id):
    improved = load_structure_by_id(improved_id)
    new_id = str(uuid4())

    improved["id"] = new_id
    improved["title"] = improved.get("title", "") + "（新規保存）"
    improved["generated_by"] = "ChatGPT改善案（別登録）"

    append_structure_log(improved, "save_as_new", f"改善案 {improved_id} を別テンプレートとして保存")

    save_structure(new_id, improved)
    return redirect(url_for('structure.edit_structure', structure_id=new_id))


@structure_bp.route('/review_repair/<original_id>/<repaired_id>')
def review_repair(original_id, repaired_id):
    original = load_structure_by_id(original_id)
    repaired = load_structure_by_id(repaired_id)

    # 差分表示用のHTMLを生成
    diff_html = get_diff_highlighted(original.get("content", ""), repaired.get("content", ""))

    # 評価（intent_match / quality_score）
    evaluations = call_claude_and_gpt(repaired.get("content", ""))
    repaired["evaluations"] = evaluations  # 直接表示用に埋め込み

    return render_template("structure_review_repair.html", original=original, repaired=repaired, diff_html=diff_html)
