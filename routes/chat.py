from flask import Blueprint, render_template, request, session, redirect, url_for
from utils.chatgpt_utils import call_chatgpt_api
from utils.structure_utils import save_structure
from utils.claude_utils import call_claude_api as call_claude
from utils.diff_utils import get_diff_highlighted
import uuid
import os
import re

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/prompt', methods=['GET', 'POST'])
def chat_prompt():
    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST':
        user_message = request.form['message']
        session['chat_history'].append({"role": "user", "content": user_message})

        assistant_response = call_chatgpt_api(session['chat_history'])
        session['chat_history'].append({"role": "assistant", "content": assistant_response})

    # ChatGPT保存
    if request.args.get("save") == "1" and session.get('chat_history'):
        structure_id = str(uuid.uuid4())[:8]
        structure = {
            "id": structure_id,
            "title": "Chat生成テンプレート",
            "description": "ChatGPTから生成されたテンプレートです。",
            "content": session['chat_history'][-1]['content']
        }
        save_structure(structure)
        return redirect(url_for('structure.edit_structure', structure_id=structure_id))

    # Claude整形＋評価＋保存
    if request.args.get("claude_save") == "1" and session.get('chat_history'):
        raw = session['chat_history'][-1]['content']
        claude_prompt = f"""
以下は構成テンプレートです。内容を整形してJSON形式で返してください。
"""
        try:
            structured = call_claude(claude_prompt)

            # 評価プロンプト（intent_match / quality_score）
            eval_prompt = f"""
以下の構成テンプレートを評価してください：

1. intent_match（0.0〜1.0）：意図の一致度
2. quality_score（0.0〜1.0）：構成の完成度

構成：

回答形式：
intent_match: 0.80
quality_score: 0.90
"""
            eval_result = call_claude(eval_prompt)
            intent_match = float(re.search(r"intent_match:\s*(\d+\.\d+)", eval_result).group(1))
            quality_score = float(re.search(r"quality_score:\s*(\d+\.\d+)", eval_result).group(1))

        except Exception as e:
            return f"<pre>Claude APIエラー: {e}</pre>"

        structure_id = str(uuid.uuid4())[:8]
        structure = {
            "id": structure_id,
            "title": "Claude整形テンプレート",
            "description": "Claudeによって整形された構成テンプレート",
            "content": structured,
            "intent_match": intent_match,
            "quality_score": quality_score
        }
        save_structure(structure)
        return redirect(url_for('structure.edit_structure', structure_id=structure_id))

    return render_template('chat_prompt.html', chat_history=session['chat_history'])

@chat_bp.route('/claude_test')
def claude_test():
    if not os.getenv("DEBUG_MODE") == "1":
        return "⚠ 開発モードでのみ利用可能", 403

    prompt = "次のJSONを整形してください:\n{ 'name': 'sample', 'age':30 }"
    result = call_claude(prompt)
    return f"<pre>{result}</pre>"

@chat_bp.route('/compare')
def compare_structures():
    if 'chat_history' not in session or len(session['chat_history']) < 2:
        return "履歴が不足しています。"

    original = session['chat_history'][-1]['content']

    claude_prompt = f"""
次の構成テンプレートを整形し、JSON形式で返してください:
"""
    try:
        transformed = call_claude(claude_prompt)
        diff_html = get_diff_highlighted(original, transformed)
    except Exception as e:
        return f"<pre>Claude APIエラー: {e}</pre>"

    return render_template("structure_compare.html",
                           original=original,
                           transformed=transformed,
                           diff_html=diff_html)
