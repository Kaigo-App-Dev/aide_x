from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from utils.structure_utils import load_structures, save_structure, load_structure_by_id
from utils.validator import validate_structure  # 必要に応じて
from utils.history_utils import extract_score_history
from datetime import datetime
from uuid import uuid4


structure_bp = Blueprint('structure', __name__, url_prefix='/structure')

@structure_bp.route('/list')
def list_structures():
    structures = load_structures()
    return render_template('structure_list.html', structures=structures)

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
        save_structure(new_structure)
        return redirect(url_for('structure.edit_structure', structure_id=new_id))
    # GET の場合は空のフォームを表示
    empty_structure = {
        "id": "",
        "title": "",
        "description": "",
        "content": "",
        "is_final": False
    }
    return render_template('edit_structure.html', structure=empty_structure)

@structure_bp.route('/edit/<structure_id>', methods=['GET', 'POST'])
def edit_structure(structure_id):
    if request.method == 'POST':
        updated_structure = {
            "id": structure_id,
            "title": request.form['title'],
            "description": request.form['description'],
            "content": request.form['content'],
            "is_final": 'is_final' in request.form  # ✅ チェックボックスの有無で判定
        }

        errors = validate_structure(updated_structure)
        if errors:
            return render_template('edit_structure.html', structure=updated_structure, errors=errors)

        save_structure(updated_structure, is_final=updated_structure["is_final"])  # ✅ 第二引数渡す
        return redirect(url_for('structure.list_structures'))

    structure = load_structure_by_id(structure_id)
    return render_template('edit_structure.html', structure=structure)

@structure_bp.route('/decide/<structure_id>', methods=['POST'])
def decide_structure(structure_id):
    structure = load_structure_by_id(structure_id)
    structure['is_final'] = True
    save_structure(structure)
    return redirect(url_for('structure.edit_structure', structure_id=structure_id))

@structure_bp.route('/diff/<structure_id>/<version_id>')
def show_diff(structure_id, version_id):
    from utils.structure_utils import load_structure_by_id, load_structure_version
    from utils.diff_utils import get_diff_highlighted

    current = load_structure_by_id(structure_id)
    past = load_structure_version(structure_id, version_id)  # 要実装

    if not current or not past:
        return "構成またはバージョンが見つかりません", 404

    diff_html = get_diff_highlighted(past['content'], current['content'])

    return render_template("structure_diff.html",
                           current=current['content'],
                           past=past['content'],
                           diff_html=diff_html)

@structure_bp.route('/evaluate/<structure_id>')
def evaluate_structure(structure_id):
    from utils.structure_utils import load_structure_by_id, save_structure
    from utils.structure_validator import evaluate_structure_content

    structure = load_structure_by_id(structure_id)
    score_result = evaluate_structure_content(structure["content"])

    # 結果を保存
    structure["intent_match"] = score_result["intent_match"]
    structure["quality_score"] = score_result["quality_score"]
    structure["intent_reason"] = score_result["intent_reason"]
    save_structure(structure, is_final=structure.get("is_final", False))

    return render_template("evaluate_structure.html", structure=structure, result=score_result)

@structure_bp.route('/claude_evaluate/<structure_id>')
def claude_evaluate_structure(structure_id):
    from utils.structure_utils import load_structure_by_id, save_structure
    from utils.claude_utils import get_structure_intent_reason

    structure = load_structure_by_id(structure_id)
    reason = get_structure_intent_reason(structure["content"])

    structure["intent_reason"] = reason
    save_structure(structure)  # ✅ 修正済み：順序・内容ともに正しい

    return render_template("evaluate_structure.html", structure=structure, result={
        "intent_match": structure.get("intent_match"),
        "quality_score": structure.get("quality_score"),
        "intent_reason": reason
    })

@structure_bp.route('/improve/<structure_id>')
def improve_structure(structure_id):
    from utils.structure_utils import load_structure_by_id, save_structure
    from utils.chatgpt_utils import call_chatgpt
    import json

    structure = load_structure_by_id(structure_id)

    prompt = f"""
以下の構成テンプレートは、意図との一致度や構成の品質スコアが低めです。
改善点を考慮し、より適切な構成テンプレートに修正してください。
そのままJSON形式で出力してください。

構成テンプレート:
{structure["content"]}
"""

    improved_json = call_chatgpt(prompt)

    # 改善案として仮保存（元の構成と比較可能に）
    save_structure(f"{structure_id}_improved", {
        "id": f"{structure_id}_improved",
        "title": structure["title"] + "（改善案）",
        "content": improved_json,
        "from": structure_id,
        "generated_by": "ChatGPT改善提案"
    })

    # 🔁 ここを書き換える！
    return redirect(url_for('chat.compare') + f"?original={structure_id}&modified={structure_id}_improved")

@structure_bp.route('/adopt/<improved_id>/<original_id>', methods=['POST'])
def adopt_structure(improved_id, original_id):
    from utils.structure_utils import load_structure_by_id, save_structure, append_structure_log

    improved = load_structure_by_id(improved_id)
    original = load_structure_by_id(original_id)

    original["content"] = improved["content"]
    original["title"] = improved["title"] + "（採用）"
    original["generated_by"] = "ChatGPT改善採用"

    # ✅ ログ追加
    append_structure_log(original, "adopt", f"構成 {improved_id} を採用")

    save_structure(original_id, original)
    return redirect(url_for('structure.edit_structure', structure_id=original_id))

@structure_bp.route('/discard/<improved_id>', methods=['POST'])
def discard_structure(improved_id):
    import os
    from utils.structure_utils import get_structure_path, load_structure_by_id, append_structure_log, save_structure

    path = get_structure_path(improved_id)

    if os.path.exists(path):
        structure = load_structure_by_id(improved_id)
        append_structure_log(structure, "discard", "改善案を不採用にした")
        save_structure(improved_id, structure)

        os.remove(path)

    return redirect(url_for('structure.list_structures'))

@structure_bp.route('/save_as_new/<improved_id>', methods=['POST'])
def save_as_new_structure(improved_id):
    from utils.structure_utils import load_structure_by_id, save_structure, append_structure_log
    from uuid import uuid4

    improved = load_structure_by_id(improved_id)

    new_id = str(uuid4())
    improved["id"] = new_id
    improved["title"] = improved.get("title", "") + "（新規保存）"
    improved["generated_by"] = "ChatGPT改善案（別登録）"

    append_structure_log(improved, "save_as_new", f"改善案 {improved_id} を別テンプレートとして保存")

    save_structure(improved, is_final=False)
    return redirect(url_for('structure.edit_structure', structure_id=new_id))

@structure_bp.route('/restore/<structure_id>', methods=['POST'])
def restore_from_history(structure_id):
    from utils.structure_utils import load_structure_by_id, save_structure, append_structure_log

    structure = load_structure_by_id(structure_id)
    timestamp = request.form.get("timestamp")

    # 該当の履歴エントリを検索
    target = next((h for h in structure.get("history", []) if h.get("timestamp") == timestamp), None)

    if target and "snapshot" in target:
        snapshot = target["snapshot"]
        structure["content"] = snapshot.get("content", "")
        structure["title"] = snapshot.get("title", "")
        structure["description"] = snapshot.get("description", "")

        append_structure_log(structure, "restore", f"{timestamp} のスナップショットから復元")

        save_structure(structure)

    return redirect(url_for('structure.edit_structure', structure_id=structure_id))


@structure_bp.route('/history')
def history():
    all_structures = load_structures()

    # フィルタ条件取得
    keyword = request.args.get('keyword', '').lower()
    sort_key = request.args.get('sort', 'updated_at')
    reverse = request.args.get('order', 'desc') == 'desc'

    # 新規追加のフィルタ条件
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    is_final_filter = request.args.get('is_final', '')  # 'true', 'false', ''

    # キーワード検索（タイトル or ID）
    if keyword:
        all_structures = [
            s for s in all_structures
            if keyword in s.get('title', '').lower() or keyword in s.get('id', '').lower()
        ]

    # 日付フィルタ
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

    # is_final フィルタ
    if is_final_filter.lower() == 'true':
        all_structures = [s for s in all_structures if s.get('is_final', False)]
    elif is_final_filter.lower() == 'false':
        all_structures = [s for s in all_structures if not s.get('is_final', False)]

    # ソート
    if all_structures and sort_key in all_structures[0]:
        all_structures.sort(key=lambda x: x.get(sort_key), reverse=reverse)

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

    # JSONを見やすく整形
    import json
    content_json = json.dumps(structure, ensure_ascii=False, indent=2)

    return render_template('structure_history_detail.html',
                           structure=structure,
                           content_json=content_json)

@structure_bp.route('/score_history/<structure_id>')
def show_score_history(structure_id):
    """
    指定された構成テンプレートIDに対するスコア推移履歴（JSON形式）を返す
    """
    history = extract_score_history(structure_id)
    return jsonify(history)