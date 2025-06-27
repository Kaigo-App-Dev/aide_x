from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import logging
import json
import os

from src.structure.utils import load_structure_by_id, save_structure
from src.structure.evaluation import evaluate_with_claude, evaluate_with_chatgpt
from src.common.logging_utils import get_logger
from routes.structure.base_routes import structure_bp

logger = get_logger("root")

@structure_bp.route("/evaluate/<structure_id>", methods=["GET"])
def evaluate_structure(structure_id):
    """構成の評価を実行する"""
    logger.info(f"🔍 構成評価開始 - structure_id: {structure_id}")
    
    structure = load_structure_by_id(structure_id)
    if not structure:
        logger.warning(f"❌ 構成が見つかりません - structure_id: {structure_id}")
        flash(f"構成 '{structure_id}' が見つかりません ❌", "danger")
        return redirect(url_for("structure.list_structures"))

    try:
        # 構成情報をログに出力
        title = structure.get("title", "タイトルなし")
        user_id = getattr(current_user, 'id', 'anonymous') if current_user else 'anonymous'
        logger.info(f"📋 評価対象構成 - ID: {structure_id}, タイトル: {title}, ユーザー: {user_id}")
        
        # contentがstrならdictに変換
        if isinstance(structure.get("content"), str):
            try:
                structure["content"] = json.loads(structure["content"])
                logger.debug("✅ structure['content'] を JSON dict に変換しました")
            except Exception as e:
                logger.error(f"❌ structure['content'] の JSON パース失敗 - structure_id: {structure_id}, error: {str(e)}")
                structure["content"] = {}

        logger.info("🤖 Claude による評価を実行中...")
        flash("Claude による評価を実行中...", "info")
        claude_result = evaluate_with_claude(structure)
        logger.info(f"✅ Claude評価完了 - intent_match: {claude_result.get('intent_match', 0)}, quality_score: {claude_result.get('quality_score', 0)}")

        logger.info("🤖 ChatGPT による評価を実行中...")
        flash("ChatGPT による評価を実行中...", "info")
        chatgpt_result = evaluate_with_chatgpt(structure)
        logger.info(f"✅ ChatGPT評価完了 - intent_match: {chatgpt_result.get('intent_match', 0)}, quality_score: {chatgpt_result.get('quality_score', 0)}")

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

        save_structure(structure_id, structure)
        logger.info(f"✅ 構成評価・保存完了 - structure_id: {structure_id}, タイトル: {title}")
        flash("✅ 評価と履歴保存が完了しました（Claude＋ChatGPT）", "success")

    except Exception as e:
        logger.exception(f"❌ 構成評価中にエラーが発生 - structure_id: {structure_id}, error: {str(e)}")
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
