"""
Chat routes for the application
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from flask_login import login_required, current_user
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, cast

from src.exceptions import APIRequestError, ResponseFormatError
from src.types import (
    StructureDict,
    EvaluationResult,
    StructureHistory,
    LLMResponse,
    ChatHistory,
    MessageParam,
    MessageParamList
)
from src.structure.utils import (
    validate_structure,
    normalize_structure_format,
    save_structure,
    load_structure,
    append_structure_log
)
from src.llm.providers.claude import call_claude_api as call_claude
from src.llm.providers.claude import call_claude_evaluation
from src.llm.controller import controller
from src.llm.prompts import prompt_manager

# --- ChatGPT・構成生成 ---
from src.llm.hub import safe_generate_and_evaluate

# --- Claude評価・フィードバック ---
from src.structure.evaluation import evaluate_with_claude, call_claude_and_gpt

# --- 構成保存・差分処理 ---
from src.diff import get_diff_highlighted

from src.llm.providers.base import ChatMessage

logger = logging.getLogger(__name__)

# Blueprintの定義
chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

def get_session() -> Optional[Dict[str, Any]]:
    """
    現在のセッション情報を取得する
    
    Returns:
        Optional[Dict[str, Any]]: セッション情報（chat_historyを含む）
    """
    if not session:
        return None
    
    # セッションの初期化（必要な場合）
    if "chat_history" not in session:
        session["chat_history"] = []
    if "stage" not in session:
        session["stage"] = "chat"
    if "summary" not in session:
        session["summary"] = ""
    
    return {
        "chat_history": session["chat_history"],
        "stage": session["stage"],
        "summary": session["summary"]
    }

def save_chat_response(session_data: Dict[str, Any], user_message: str, ai_response: str) -> None:
    """
    チャット応答をセッションに保存する
    
    Args:
        session_data (Dict[str, Any]): セッション情報
        user_message (str): ユーザーのメッセージ
        ai_response (str): AIの応答
    """
    if not session_data:
        return
    
    chat_history = session_data.get("chat_history", [])
    chat_history.extend([
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": ai_response}
    ])
    
    # セッションの更新
    session["chat_history"] = chat_history
    session["summary"] = extract_summary_from_chat(chat_history)

def extract_summary_from_chat(chat_history: List[Dict[str, str]]) -> str:
    """
    チャット履歴から要約を抽出する
    
    Args:
        chat_history (List[Dict[str, str]]): チャット履歴
    
    Returns:
        str: 抽出された要約
    """
    if not chat_history:
        return "No summary available."
    
    # 最後のassistant応答の冒頭を要約として使用
    for entry in reversed(chat_history):
        if entry["role"] == "assistant":
            content = entry["content"].strip()
            if content:
                # 最初の段落または文を要約として使用
                summary = content.split("\n")[0].strip()
                return summary if summary else "No summary available."
    
    return "No summary available."

class ChatForm(FlaskForm):
    """Chat form for message input."""
    message: str = StringField('Message', validators=[DataRequired()])

@chat_bp.route("/chat", methods=["POST"])
def chat_prompt():
    """チャットプロンプトの処理"""
    try:
        # リクエストデータの取得
        data = request.get_json()
        user_message = data.get("message", "")
        chat_history = data.get("chat_history", [])

        # セッションの取得
        session_data = get_session()
        if not session_data:
            return jsonify({"error": "セッションが見つかりません"}), 404

        print("🧭 controller.call() を呼び出す前です")
        try:
            # プロンプトの取得
            prompt = cast(str, prompt_manager.get("chatgpt", "chat"))
            variables = {
                "user_input": user_message,
                "chat_history": json.dumps(chat_history, ensure_ascii=False)
            }
            
            # AIControllerを使用して応答を取得
            response = controller.call(
                provider="chatgpt",
                prompt=prompt,
                variables=variables
            )

            # 応答の保存
            save_chat_response(session_data, user_message, response)

            return jsonify({
                "response": response,
                "summary": extract_summary_from_chat(chat_history)
            })

        except Exception as e:
            logger.exception("❌ チャット処理中にエラーが発生しました")
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        logger.exception("❌ チャット処理中にエラーが発生しました")
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/prompt", methods=["GET", "POST"])
def chat_prompt_old():
    print("[INFO] テンプレート: chat_prompt.html をレンダリングします")
    print("[INFO] 新しいchat_historyを作成します")
    print("[INFO] 新しいstageを作成します")
    
    if "chat_history" not in session:
        print("[INFO] 新しいchat_historyを作成します")
        session["chat_history"] = []
    if "stage" not in session:
        print("[INFO] 新しいstageを作成します")
        session["stage"] = "planning"

    chat_history = session["chat_history"]
    user_message = None

    # POST: ユーザー発言 → ChatGPT応答
    if request.method == "POST":
        print("[OK] POSTメソッドに入りました")
        print("📩 フォーム内容:", request.form)

        user_message = request.form.get("message")
        print("✉ ユーザー入力:", user_message)

        if user_message:
            chat_history.append({"role": "user", "content": user_message})
            print("[INFO] chat_historyに追加しました:", chat_history[-1])

            # ステージ自動変更（キーワードに応じて）
            if session["stage"] == "suggest":
                if any(k in user_message for k in ["構成", "提案", "出して"]):
                    print("🔄 ステージを 'generate' に変更します")
                    session["stage"] = "generate"

            print("🧭 controller.call() を呼び出す前です")
            try:
                # プロンプトの取得
                prompt = prompt_manager.get("chatgpt", "chat", user_input=user_message)
                
                # AIControllerを使用して応答を取得
                response = controller.call(
                    "chatgpt",
                    chat_history,
                    prompt=prompt,
                    stage=session.get("stage")
                )
                print("🧭 応答:", response)
                chat_history.append({"role": "assistant", "content": response})

                # コードブロックの検出
                if "```" in response:
                    print("📦 コードブロックを検出しました")
                    session["stage"] = "generate"

                    # ✅ ChatGPT出力から構成テンプレート(JSON)を抽出
                    try:
                        import re, json
                        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
                        if json_match:
                            parsed_content = json.loads(json_match.group(1))
                        else:
                            parsed_content = json.loads(response)
                    except Exception as e:
                        print("⚠ JSONパースエラー:", str(e))
                        parsed_content = {"⚠️ エラー": f"構成のパースに失敗しました: {str(e)}"}

                    structure = {
                        "title": "仮タイトル",
                        "description": "仮の説明",
                        "content": parsed_content
                    }

                    # Claudeによる評価
                    evaluation = get_claude_intent_reason(
                        structure=structure,
                        chat_history=chat_history,
                        raw_output=response
                    )

                    chat_history.append({
                        "role": "analyzer",
                        "content": f"🧠 Claude評価理由: {evaluation['intent_reason']}"
                    })

                    session["structure"] = structure
                    session.modified = True
            except Exception as e:
                print("⚠ エラーが発生しました:", str(e))
                error_message = f"申し訳ありません。エラーが発生しました: {str(e)}"
                chat_history.append({"role": "assistant", "content": error_message})
        else:
            print("⚠ messageが空です")

        session["chat_history"] = chat_history
        session.modified = True
        print("🔄 セッションを更新しました")
        return redirect(url_for("chat.chat_prompt"))

    # GET with ?confirm=1 → Claude評価＋構成表示
    structure = None
    if request.args.get("confirm"):
        print("🔍 confirmパラメータを検出しました")
        result = safe_generate_and_evaluate(chat_history)
        structure = result.get("structure")
        evaluation = result.get("evaluation")

        if evaluation:
            print("📊 評価結果を取得しました")
            chat_history.append({
                "role": "analyzer",
                "content": f"💬 Claudeによる評価:\n"
                           f"- 意図一致度: {int(evaluation['intent_match'] * 100)} / 100\n"
                           f"- 品質スコア: {int(evaluation['quality_score'] * 100)} / 100\n"
                           f"- 理由: {evaluation['intent_reason']}"
            })

            score = int(evaluation['intent_match'] * 100)
            if score >= 80:
                comment = "✅ この構成はかなり良さそうです！このまま出力に進みましょうか？"
            elif score >= 50:
                comment = "💡 概ね合っていますが、少し調整してみますか？"
            else:
                comment = "⚠️ 少し意図とズレがあるようです。構成を見直しましょう。"

            chat_history.append({"role": "analyzer", "content": comment})
            session["structure"] = structure
            session["stage"] = "confirmed"
            session.modified = True
            print("🔄 セッションを更新しました（評価後）")

    print("🎨 テンプレートをレンダリングします")
    return render_template(
        "chat_prompt.html",
        chat_history=chat_history,
        stage=session.get("stage"),
        user_requirements=session.get("structure"),
        structure=session.get("structure")
    )

@chat_bp.route("/reset")
def chat_reset():
    session.pop("chat_history", None)
    session.pop("stage", None)
    session.pop("structure", None)
    flash("チャットセッションをリセットしました。", "success")
    return redirect(url_for("chat.chat_prompt"))

@chat_bp.route("/claude_test")
def chat_claude_test():
    structure = session.get("structure")
    if not structure:
        flash("構成が見つかりません。", "danger")
        return redirect(url_for("chat.chat_prompt"))

    evaluation_result = call_claude_evaluation(structure)
    session["evaluation_result"] = evaluation_result
    session.modified = True

    session["chat_history"].append({
        "role": "analyzer",
        "content": f"✅ Claude評価結果:\n- 意図一致度: {evaluation_result['score']}\n- コメント: {evaluation_result['comment']}"
    })
    return redirect(url_for("chat.chat_prompt"))

@chat_bp.route('/compare')
def compare_structures():
    if 'chat_history' not in session or len(session['chat_history']) < 2:
        return "履歴が不足しています。"

    original = session['chat_history'][-1]['content']
    claude_prompt = "次の構成テンプレートを整形し、JSON形式で返してください:\n" + original

    try:
        transformed = call_claude(claude_prompt)
        diff_html = get_diff_highlighted(original, transformed)
    except Exception as e:
        return f"<pre>Claude APIエラー: {e}</pre>"

    return render_template("structure_compare.html",
                           original=original,
                           transformed=transformed,
                           diff_html=diff_html)

@chat_bp.route("/chat/save", methods=["POST"])
def save_structure_route():
    """
    チャット履歴から構造体を保存する
    
    Returns:
        Response: リダイレクトまたはエラーレスポンス
    """
    chat_history_json = request.form.get("chat_history_json")
    if not chat_history_json:
        flash("構成保存に失敗しました：履歴がありません", "danger")
        return redirect(url_for("chat.chat_prompt"))

    try:
        raw_data = json.loads(chat_history_json)
    except json.JSONDecodeError as e:
        flash(f"構成保存に失敗しました（形式エラー）: {e}", "danger")
        logger.error(f"[JSON ERROR] 入力内容:\n{chat_history_json}\n")
        return redirect(url_for("chat.chat_prompt"))

    # 構造体の正規化
    try:
        structure = normalize_structure_format(raw_data)
    except Exception as e:
        flash(f"構成の正規化に失敗しました: {e}", "danger")
        logger.error(f"[NORMALIZE ERROR] 入力内容:\n{raw_data}\n")
        return redirect(url_for("chat.chat_prompt"))

    # 構造体の検証
    is_valid, errors = validate_structure(structure)
    if not is_valid:
        flash(f"構成の検証に失敗しました: {', '.join(errors)}", "danger")
        logger.error(f"[VALIDATION ERROR] 入力内容:\n{structure}\n")
        return redirect(url_for("chat.chat_prompt"))

    # 構造体の保存
    try:
        structure_id = save_structure(structure)
        session["structure_id"] = structure_id
        flash("構成を保存しました ✅", "success")
        return redirect(url_for("chat.chat_prompt"))
    except Exception as e:
        flash(f"構成の保存に失敗しました: {e}", "danger")
        logger.error(f"[SAVE ERROR] 入力内容:\n{structure}\n")
        return redirect(url_for("chat.chat_prompt"))

@chat_bp.route("/structure/test", methods=["POST"])
def test_structure():
    """
    構造体のテスト評価を行う
    
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

        # 評価の実行
        evaluation_result = evaluate_with_claude(structure)
        
        return jsonify({
            "success": True,
            "evaluation": evaluation_result
        })

    except Exception as e:
        logger.exception("構造体のテスト評価中にエラーが発生しました")
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/structure/improve", methods=["POST"])
def improve_structure():
    """
    構造体の改善提案を行う
    
    Returns:
        Response: JSONレスポンス
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "リクエストデータがありません"}), 400

        structure = data.get("structure")
        if not structure:
            return jsonify({"error": "構造体が指定されていません"}), 400

        # 改善提案の生成
        improvement_result = call_claude_and_gpt(structure)
        
        # 改善結果の保存
        session["improvement_result"] = improvement_result
        session.modified = True

        return jsonify({
            "success": True,
            "improvement": improvement_result
        })

    except Exception as e:
        logger.exception("構造体の改善提案中にエラーが発生しました")
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/structure/repair/<structure_id>", methods=["POST"])
def repair_structure(structure_id: str):
    """
    構造体の修復を行う
    
    Args:
        structure_id (str): 修復対象の構造体ID
    
    Returns:
        Response: JSONレスポンス
    """
    try:
        # 構造体の読み込み
        structure = load_structure(structure_id)
        if not structure:
            return jsonify({"error": "構造体が見つかりません"}), 404

        # 修復の実行
        repair_result = call_claude_and_gpt(structure)
        
        # 修復結果の保存
        repaired_structure = repair_result.get("structure", structure)
        new_structure_id = save_structure(repaired_structure)
        
        return jsonify({
            "success": True,
            "structure_id": new_structure_id,
            "repair": repair_result
        })

    except Exception as e:
        logger.exception("構造体の修復中にエラーが発生しました")
        return jsonify({"error": str(e)}), 500 