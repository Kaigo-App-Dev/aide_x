from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import logging
import json
import os

from src.structure.utils import load_structure_by_id, save_structure
from src.structure.evaluation import evaluate_with_claude, evaluate_with_chatgpt

logger = logging.getLogger(__name__)

@structure_bp.route("/evaluate/<structure_id>", methods=["GET"])
def evaluate_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        flash(f"構成 '{structure_id}' が見つかりません ❌", "danger")
        return redirect(url_for("structure.list_structures"))

    try:
        # contentがstrならdictに変換
        if isinstance(structure.get("content"), str):
            try:
                structure["content"] = json.loads(structure["content"])
            except Exception:
                logger.error("structure['content'] の JSON パース失敗")
                structure["content"] = {}

        logger.debug("structure['content'] を JSON dict に変換しました。")

        flash("Claude による評価を実行中...", "info")
        claude_result = evaluate_with_claude(structure)

        flash("ChatGPT による評価を実行中...", "info")
        chatgpt_result = evaluate_with_chatgpt(structure)

        structure["evaluations"] = {
            "claude": claude_result,
            "chatgpt": chatgpt_result
        }

        if "evaluations_history" not in structure:
            structure["evaluations_history"] = []

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        structure["evaluations_history"].append({
            "model": "claude",
            "intent_match": claude_result.get("intent_match", 0),
            "quality_score": claude_result.get("quality_score", 0),
            "timestamp": now
        })
        structure["evaluations_history"].append({
            "model": "chatgpt",
            "intent_match": chatgpt_result.get("intent_match", 0),
            "quality_score": chatgpt_result.get("quality_score", 0),
            "timestamp": now
        })

        # ログ追加
        logger.debug(f"保存直前の structure['content'] 型: {type(structure['content'])}")
        content_preview = json.dumps(structure['content'], ensure_ascii=False, default=str)[:100]
        logger.debug(f"保存直前の structure['content'] 内容プレビュー: {content_preview}")


        save_structure(structure)
        flash("✅ 評価と履歴保存が完了しました（Claude＋ChatGPT）", "success")

    except Exception as e:
        logger.error(f"保存失敗: {e}")
        flash(f"⚠ 保存失敗：構造テンプレートが不正なJSONです。", "danger")

    return redirect(url_for("structure.edit_structure", structure_id=structure_id))

@structure_bp.route("/structure/graph/<structure_id>")
def graph_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        flash(f"構成 '{structure_id}' が見つかりません ❌", "danger")
        return redirect(url_for("structure.list_structures"))

    history = structure.get("evaluations_history", [])

    return render_template("structure_graph.html",
                           structure_id=structure_id,
                           title=structure.get("title", ""),
                           history=history)
