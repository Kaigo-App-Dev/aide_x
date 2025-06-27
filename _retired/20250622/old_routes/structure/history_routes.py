from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
from datetime import datetime
import json
import io
from . import structure_bp
from src.structure.utils import (
    load_structures, load_structure_by_id,
    save_structure, append_structure_log
)
from src.common.history import extract_score_history
from src.common.db import get_db
from src.structure.feedback import call_claude
from src.common.diff import get_diff_highlighted
from src.structure.history_manager import (
    load_structure_history,
    get_history_summary
)
import logging

logger = logging.getLogger(__name__)

@structure_bp.route('/history')
def history():
    all_structures = load_structures()

    # フィルタ取得
    keyword = request.args.get('keyword', '').lower()
    sort_key = request.args.get('sort', 'updated_at')
    reverse = request.args.get('order', 'desc') == 'desc'
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    is_final_filter = request.args.get('is_final', '')

    # フィルタ処理
    if keyword:
        all_structures = [
            s for s in all_structures
            if keyword in s.get('title', '').lower() or keyword in s.get('id', '').lower()
        ]

    def in_date_range(s):
        if not start_date_str and not end_date_str:
            return True
        try:
            updated_at = datetime.strptime(s.get('updated_at', '1970-01-01'), '%Y-%m-%d %H:%M:%S')
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                if updated_at < start_date:
                    return False
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                if updated_at > end_date:
                    return False
            return True
        except Exception:
            return True

    all_structures = [s for s in all_structures if in_date_range(s)]

    if is_final_filter.lower() == 'true':
        all_structures = [s for s in all_structures if s.get('is_final', False)]
    elif is_final_filter.lower() == 'false':
        all_structures = [s for s in all_structures if not s.get('is_final', False)]

    if all_structures and sort_key in all_structures[0]:
        all_structures.sort(key=lambda x: x.get(sort_key, ''), reverse=reverse)

    return render_template('structure_history.html',
                           structures=all_structures,
                           keyword=keyword,
                           sort_key=sort_key,
                           order='desc' if reverse else 'asc',
                           start_date=start_date_str,
                           end_date=end_date_str,
                           is_final_filter=is_final_filter)


@structure_bp.route('/history/<structure_id>')
def history_detail(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "データが見つかりません", 404

    content_json = json.dumps(structure, ensure_ascii=False, indent=2)

    return render_template('structure_history_detail.html',
                           structure=structure,
                           content_json=content_json)


@structure_bp.route('/restore/<structure_id>', methods=['POST'])
def restore_from_history(structure_id):
    structure = load_structure_by_id(structure_id)
    timestamp = request.form.get("timestamp")

    target = next((h for h in structure.get("history", []) if h.get("timestamp") == timestamp), None)

    if target and "snapshot" in target:
        snapshot = target["snapshot"]
        structure["content"] = snapshot.get("content", "")
        structure["title"] = snapshot.get("title", "")
        structure["description"] = snapshot.get("description", "")
        append_structure_log(structure, "restore", f"{timestamp} のスナップショットから復元")
        save_structure(structure_id, structure)

    return redirect(url_for('structure.edit_structure', structure_id=structure_id))


@structure_bp.route('/score_history/<structure_id>')
def show_score_history(structure_id):
    history = extract_score_history(structure_id)
    return json.dumps(history, ensure_ascii=False)


@structure_bp.route("/history/delete/<int:structure_id>", methods=["POST"])
def delete_structure(structure_id):
    db = get_db()
    db.execute("DELETE FROM structure_history WHERE id = ?", (structure_id,))
    db.commit()
    flash("構成履歴を削除しました。")
    return redirect(url_for("structure.history"))


@structure_bp.route('/history/diff/<structure_id>/<timestamp>')
def view_structure_diff(structure_id, timestamp):
    structure = load_structure_by_id(structure_id)
    current = structure.get("content", "")
    history = structure.get("history", [])

    target = next((h for h in history if h.get("timestamp") == timestamp), None)
    snapshot = target.get("snapshot", {}).get("content", "") if target else ""

    diff_html = get_diff_highlighted(snapshot, current)

    return render_template("structure_diff.html",
                           structure_id=structure_id,
                           timestamp=timestamp,
                           past=snapshot,
                           current=current,
                           diff_html=diff_html)


@structure_bp.route('/repair/<structure_id>', methods=['POST'])
def repair_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    if not structure:
        return "構成が見つかりません", 404

    evaluation = call_claude(structure.get("content", ""))
    logs = structure.get("logs", [])

    return render_template('edit_structure.html',
                           structure=structure,
                           evaluation=evaluation,
                           logs=logs,
                           errors=[])


@structure_bp.route("/history/<structure_id>")
def view_structure_history(structure_id):
    """
    構造の履歴を表示する
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        str: 履歴表示ページのHTML
    """
    try:
        # 履歴データを読み込み
        history_data = load_structure_history(structure_id)
        
        if not history_data:
            return render_template(
                "structure/history.html",
                structure_id=structure_id,
                history_data=None,
                summary=None,
                error="履歴が見つかりません"
            )
        
        # 履歴サマリーを取得
        summary = get_history_summary(structure_id)
        
        return render_template(
            "structure/history.html",
            structure_id=structure_id,
            history_data=history_data,
            summary=summary,
            error=None
        )
        
    except Exception as e:
        logger.error(f"履歴表示中にエラーが発生: {str(e)}")
        return render_template(
            "structure/history.html",
            structure_id=structure_id,
            history_data=None,
            summary=None,
            error=f"履歴の表示中にエラーが発生しました: {str(e)}"
        )

@structure_bp.route("/api/history/<structure_id>")
def get_structure_history_api(structure_id):
    """
    構造の履歴をJSON形式で取得するAPI
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        dict: 履歴データのJSONレスポンス
    """
    try:
        # 履歴データを読み込み
        history_data = load_structure_history(structure_id)
        
        if not history_data:
            return jsonify({
                "success": False,
                "error": "履歴が見つかりません",
                "structure_id": structure_id
            }), 404
        
        return jsonify({
            "success": True,
            "data": history_data,
            "structure_id": structure_id
        })
        
    except Exception as e:
        logger.error(f"履歴API呼び出し中にエラーが発生: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"履歴の取得中にエラーが発生しました: {str(e)}",
            "structure_id": structure_id
        }), 500

@structure_bp.route("/api/history/<structure_id>/summary")
def get_structure_history_summary_api(structure_id):
    """
    構造の履歴サマリーをJSON形式で取得するAPI
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        dict: 履歴サマリーのJSONレスポンス
    """
    try:
        # 履歴サマリーを取得
        summary = get_history_summary(structure_id)
        
        return jsonify({
            "success": True,
            "data": summary,
            "structure_id": structure_id
        })
        
    except Exception as e:
        logger.error(f"履歴サマリーAPI呼び出し中にエラーが発生: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"履歴サマリーの取得中にエラーが発生しました: {str(e)}",
            "structure_id": structure_id
        }), 500

