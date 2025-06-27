"""
統合インターフェース用ルート

このモジュールは、構成編集、AI評価、履歴表示を1つの画面で統合するためのルートを提供します。
"""

from flask import Blueprint, render_template, request, jsonify, session
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, cast, Sequence, TypedDict, Literal, Union
import logging
import traceback

from src.structure.utils import load_structure_by_id, save_structure, StructureDict
from src.structure.history_manager import save_structure_history, load_structure_history, get_history_summary
from src.structure.evaluation import evaluate_with_claude, evaluate_with_chatgpt
from src.common.logging_utils import get_logger, log_exception, log_request
from src.llm.client import client as llm_client
from src.llm.providers.base import ChatMessage
from src.llm.controller import AIController, controller
from src.llm.evaluator import evaluate_structure_with, EvaluationResult
from src.types import MessageParam, safe_cast_message_param, safe_cast_dict, safe_cast_str
from src.structure.evaluator import evaluate_structure_with
from src.llm.evaluators import ClaudeEvaluator
from src.llm.evaluators.common import EvaluationResult
from src.utils.files import extract_json_part

logger = logging.getLogger(__name__)

# ログ設定の強化
logger.setLevel(logging.DEBUG)

# ファイルハンドラーの追加（logs/unified_debug.logに出力）
import os
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

file_handler = logging.FileHandler(os.path.join(log_dir, "unified_debug.log"), encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# コンソールハンドラーの追加
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class ExtendedStructureDict(TypedDict):
    """拡張された構造データ型"""
    id: str
    title: str
    description: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    history: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]

unified_bp = Blueprint('unified', __name__, url_prefix='/unified')

def chat_message_to_dict(message: ChatMessage) -> Dict[str, str]:
    """ChatMessageをDict[str, str]に変換する"""
    return {
        "role": message.role,
        "content": message.content
    }

def message_param_to_chat_message(message: MessageParam) -> ChatMessage:
    """MessageParamをChatMessageに変換する"""
    return ChatMessage(
        role=message["role"],
        content=message["content"]
    )

def dict_to_structure_dict(data: Dict[str, Any], structure_id: str) -> StructureDict:
    """Dict[str, Any]をStructureDictに変換する"""
    structure_dict: Dict[str, Any] = {
        "id": structure_id,
        "title": safe_cast_str(data.get("title", "")),
        "description": safe_cast_str(data.get("description", "")),
        "content": safe_cast_dict(data.get("content", {}))
    }
    
    # Optional fields
    if data.get("metadata") is not None:
        structure_dict["metadata"] = safe_cast_dict(data["metadata"])
    if data.get("history") is not None:
        structure_dict["history"] = data["history"]
    
    return cast(StructureDict, structure_dict)

def create_message_param(role: str, content: str, name: Optional[str] = None, type: Optional[str] = None) -> MessageParam:
    """MessageParamを作成する"""
    message: Dict[str, Any] = {
        "role": role,
        "content": content
    }
    if name is not None:
        message["name"] = name
    if type is not None:
        message["type"] = type
    return cast(MessageParam, message)

def evaluate_and_append_message(structure: Dict[str, Any]) -> None:
    """
    Claudeで構成を評価し、結果をメッセージに追加する
    
    Args:
        structure: 構造データ
    """
    try:
        # structure["content"]が文字列の場合はJSONとしてパース
        structure_content = structure.get("content")
        if isinstance(structure_content, str):
            try:
                import json
                structure_content = json.loads(structure_content)
                structure["content"] = structure_content
                logger.info(f"✅ evaluate_and_append_message: structure['content']をJSONからdictに変換: {type(structure_content)}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ evaluate_and_append_message: structure['content']のJSONパースに失敗: {str(e)}")
                # JSONパースに失敗した場合はエラーメッセージを追加して終了
                structure.setdefault("messages", []).append(
                    create_message_param(
                        role="assistant",
                        content="⚠️ 構成データがJSON形式でなかったため、Claude評価をスキップしました",
                        name="claude",
                        type="note"
                    )
                )
                return
        
        logger.info("🧠 Claude評価開始")
        result = evaluate_structure_with(provider_name="claude", structure=structure)
        
        if not result:
            logger.error("❌ 評価結果が取得できませんでした")
            structure.setdefault("messages", []).append(
                create_message_param(
                    role="assistant",
                    content="⚠️ 評価結果が取得できませんでした",
                    name="claude",
                    type="note"
                )
            )
            return

        # 評価結果を文字列として取得
        evaluation_content = str(result)
        
        # メッセージ配列の初期化と追加
        structure.setdefault("messages", []).append(
            create_message_param(
                role="assistant",
                content=evaluation_content,
                name="claude",
                type="note"
            )
        )
        
        logger.info("✅ Claude評価完了")
        
    except Exception as e:
        logger.error(f"❌ Claude評価エラー: {str(e)}")
        # エラーメッセージをチャットに追加
        structure.setdefault("messages", []).append(
            create_message_param(
                role="assistant",
                content=f"⚠️ 構成の評価中にエラーが発生しました:\n{str(e)}",
                name="claude",
                type="note"
            )
        )

@unified_bp.route('/<structure_id>')
def unified_interface(structure_id):
    """
    統合インターフェースを表示する
    
    Args:
        structure_id: 構成のID
        
    Returns:
        str: 統合インターフェースのHTML
    """
    logger.info(f"🌐 統合インターフェース表示開始 - structure_id: {structure_id}")
    
    try:
        # ステップ1: 構成データの読み込み
        logger.info(f"📂 ステップ1: 構成データ読み込み開始 - structure_id: {structure_id}")
        
        # 複数のパスで構成ファイルを探す
        possible_paths = [
            f"data/default/{structure_id}.json",
            f"structures/{structure_id}.json",
            f"data/{structure_id}.json",
            f"data/default/{structure_id}.json"
        ]
        
        structure = None
        used_path = None
        
        for path in possible_paths:
            logger.debug(f"🔍 パス確認: {path}")
            if os.path.exists(path):
                logger.info(f"✅ 構成ファイル発見: {path}")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        structure = json.load(f)
                    used_path = path
                    break
                except Exception as e:
                    logger.error(f"❌ ファイル読み込みエラー {path}: {str(e)}")
                    continue
        
        if not structure:
            logger.error(f"❌ 構成ファイルが見つかりません - structure_id: {structure_id}")
            logger.error(f"❌ 確認したパス: {possible_paths}")
            
            # 404エラーページを返す
            return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - 構成が見つかりません</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .error-container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 600px;
        }}
        h1 {{ color: #dc3545; }}
        p {{ color: #6c757d; line-height: 1.6; }}
        .debug-info {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
            font-family: monospace;
            font-size: 12px;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            cursor: pointer;
            background: #007bff;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>404 - 構成が見つかりません</h1>
        <p>指定された構成ID「{structure_id}」のファイルが見つかりませんでした。</p>
        
        <div class="debug-info">
            <strong>デバッグ情報:</strong><br>
            確認したパス:<br>
            {chr(10).join(f"• {path}" for path in possible_paths)}<br><br>
            現在のディレクトリ: {os.getcwd()}
        </div>
        
        <p>以下の可能性があります：</p>
        <ul style="text-align: left; display: inline-block;">
            <li>構成IDが間違っている</li>
            <li>構成ファイルが削除されている</li>
            <li>ファイルパスが正しくない</li>
        </ul>
        
        <div style="margin-top: 30px;">
            <button onclick="history.back()" class="btn">← 前のページに戻る</button>
        </div>
    </div>
</body>
</html>
""", 404
        
        logger.info(f"✅ ステップ1完了: 構成データ読み込み成功 - パス: {used_path}, キー数: {len(structure)}")
        
        # ステップ2: メッセージ配列の初期化
        logger.info(f"💬 ステップ2: メッセージ配列初期化開始")
        if "messages" not in structure:
            structure["messages"] = []
            logger.info("📝 メッセージ配列を新規作成")
        else:
            logger.info(f"📝 既存メッセージ配列を使用 - 件数: {len(structure['messages'])}")
            
        # 初回アクセス時はサンプルメッセージを表示
        if not structure["messages"]:
            logger.info("👋 初回アクセス: サンプルメッセージを追加")
            structure["messages"] = [
                {
                    'role': 'assistant',
                    'content': 'こんにちは！統合インターフェースへようこそ。構成の編集や評価について何でもお聞かせください。',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            # 初期メッセージを保存
            try:
                save_structure(structure_id, structure)
                logger.info("💾 初期メッセージを保存完了")
            except Exception as save_error:
                logger.warning(f"⚠️ 初期メッセージ保存に失敗: {str(save_error)}")
        
        # ステップ3: 評価結果の取得
        logger.info(f"📊 ステップ3: 評価結果取得開始")
        evaluation = structure.get('evaluations', {})
        
        # デフォルトの評価結果を設定
        if not evaluation:
            logger.info("📊 デフォルト評価結果を設定")
            evaluation = {
                'claude': {
                    'intent_match': 0,
                    'quality_score': 0,
                    'comment': '評価が実行されていません'
                },
                'gemini': {
                    'intent_match': 0,
                    'quality_score': 0,
                    'comment': '評価が実行されていません'
                }
            }
        else:
            logger.info(f"📊 既存評価結果を使用 - プロバイダー数: {len(evaluation)}")
        
        logger.info(f"✅ 統合インターフェースデータ準備完了 - メッセージ数: {len(structure['messages'])}, 評価: {bool(evaluation)}")
        
        # ステップ4: テンプレートレンダリング
        logger.info(f"🎨 ステップ4: テンプレートレンダリング開始")
        try:
            result = render_template('structure/unified_interface.html',
                                   structure_id=structure_id,
                                   structure=structure,
                                   messages=structure['messages'],
                                   evaluation=evaluation)
            logger.info(f"✅ テンプレートレンダリング成功 - 文字数: {len(result)}")
            return result
            
        except Exception as template_error:
            logger.error(f"❌ テンプレートレンダリングエラー: {str(template_error)}")
            raise template_error
        
    except Exception as e:
        logger.exception(f"❌ 統合インターフェース表示中にエラーが発生 - structure_id: {structure_id}, error: {str(e)}")
        
        # テンプレート読み込みエラーの場合のフォールバック処理
        try:
            logger.info("🔄 500.htmlテンプレートでのフォールバック試行")
            return render_template('errors/500.html', 
                                 error=f"統合インターフェースの表示中にエラーが発生しました: {str(e)}"), 500
        except Exception as template_error:
            logger.error(f"❌ 500.htmlテンプレート読み込みにも失敗: {str(template_error)}")
            
            # 最終フォールバックHTMLを直接返す
            logger.info("🆘 最終フォールバックHTMLを返却")
            fallback_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>500 - サーバーエラー</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .error-container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
        }}
        .error-icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #dc3545;
            margin-bottom: 15px;
        }}
        p {{
            color: #6c757d;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        .error-details {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}
        .btn-primary {{
            background: #007bff;
            color: white;
        }}
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h1>500 - サーバーエラー</h1>
        <p>申し訳ありません。サーバーで予期せぬエラーが発生しました。</p>
        
        <div class="error-details">
            <strong>エラー詳細:</strong><br>
            {str(e)}<br><br>
            <strong>テンプレートエラー:</strong><br>
            {str(template_error)}
        </div>
        
        <p>以下のいずれかの方法をお試しください：</p>
        <ul style="text-align: left; display: inline-block;">
            <li>ページを再読み込みする</li>
            <li>しばらく時間をおいて再度アクセスする</li>
            <li>ブラウザのキャッシュをクリアする</li>
        </ul>
        
        <div style="margin-top: 30px;">
            <button onclick="history.back()" class="btn btn-secondary">← 前のページに戻る</button>
            <button onclick="location.reload()" class="btn btn-primary">🔄 ページを再読み込み</button>
        </div>
    </div>
</body>
</html>
"""
            return fallback_html, 500

@unified_bp.route('/<structure_id>/evaluate', methods=['POST'])
def evaluate_structure_endpoint(structure_id: str):
    """
    構成を評価するエンドポイント
    
    Args:
        structure_id: 構成のID
        
    Returns:
        Response: 評価結果のJSON
    """
    try:
        # 構造データを読み込み
        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({"error": "構成が見つかりません"}), 404
            
        # 評価を実行
        evaluate_and_append_message(structure)
        
        # 構造を保存
        structure_dict = dict_to_structure_dict(structure, structure_id)
        save_structure(structure_id, structure_dict)
        
        return jsonify({
            "success": True,
            "message": "評価が完了しました"
        })
        
    except Exception as e:
        logger.exception(f"❌ 評価処理中にエラーが発生 - structure_id: {structure_id}, error: {str(e)}")
        return jsonify({"error": f"評価処理中にエラーが発生しました: {str(e)}"}), 500

@unified_bp.route('/<structure_id>/chat', methods=['POST'])
def send_message(structure_id: str):
    """
    会話メッセージを送信するAPI
    
    Args:
        structure_id: 構成のID
        
    Returns:
        Response: 会話結果のJSON
    """
    try:
        # リクエスト情報をログ出力
        log_request(logger, request, f"send_message - structure_id: {structure_id}")
        
        logger.info(f"💬 会話メッセージ送信開始 - structure_id: {structure_id}")
        
        # JSONデータの取得
        logger.debug("📥 JSONデータ取得開始")
        try:
            data = request.get_json()
            logger.debug(f"📥 取得したデータ: {data}")
        except Exception as json_error:
            log_exception(logger, json_error, "JSONデータ取得")
            return jsonify({"error": f"JSONデータの解析に失敗しました: {str(json_error)}"}), 400
        
        if not data:
            logger.error("❌ メッセージデータがありません")
            return jsonify({"error": "メッセージデータがありません"}), 400
        
        message = data.get('message', '').strip()
        logger.info(f"📝 受信メッセージ: {message}")
        
        if not message:
            logger.error("❌ メッセージが空です")
            return jsonify({"error": "メッセージが空です"}), 400
        
        # 構造データを読み込み
        logger.debug("📂 構造データ読み込み開始")
        try:
            structure = load_structure_by_id(structure_id)
            if not structure:
                logger.error(f"❌ 構成が見つかりません: {structure_id}")
                return jsonify({"error": "構成が見つかりません"}), 404
            
            logger.info(f"✅ 構造データ読み込み成功 - キー数: {len(structure)}")
        except Exception as load_error:
            log_exception(logger, load_error, f"構造データ読み込み - structure_id: {structure_id}")
            return jsonify({"error": f"構造データの読み込みに失敗しました: {str(load_error)}"}), 500
                
        # メッセージ配列の初期化
        structure.setdefault("messages", [])
        logger.debug(f"💬 既存メッセージ数: {len(structure['messages'])}")
        
        # ユーザーメッセージを追加
        try:
            user_message = create_message_param(
                role="user",
                content=message
            )
            structure["messages"].append(user_message)
            logger.info("✅ ユーザーメッセージを追加")
        except Exception as msg_error:
            log_exception(logger, msg_error, "ユーザーメッセージ作成")
            return jsonify({"error": f"ユーザーメッセージの作成に失敗しました: {str(msg_error)}"}), 500
        
        try:
            # メッセージ履歴をChatMessage形式に変換
            logger.debug("🔄 メッセージ形式変換開始")
            try:
                chat_messages: List[ChatMessage] = [
                    message_param_to_chat_message(safe_cast_message_param(m))
                    for m in structure["messages"]
                ]
                
                # システムメッセージを追加
                system_message = ChatMessage(
                    role="system",
                    content="あなたは構成テンプレートの評価と改善を支援するAIアシスタントです。"
                )
                chat_messages = [system_message] + chat_messages
                
                # メッセージをDict[str, str]に変換
                api_messages: List[Dict[str, str]] = [chat_message_to_dict(m) for m in chat_messages]
                
                logger.info(f"🤖 ChatGPT呼び出し開始 - メッセージ数: {len(api_messages)}")
            except Exception as convert_error:
                log_exception(logger, convert_error, "メッセージ形式変換")
                return jsonify({"error": f"メッセージ形式の変換に失敗しました: {str(convert_error)}"}), 500
            
            # ChatGPT呼び出し
            try:
                response = controller.call(
                    provider="chatgpt",
                    messages=api_messages,
                    temperature=0.7
                )
                
                # responseの型に応じて処理を分岐
                response_content = (
                    response.get('content', '') if isinstance(response, dict)
                    else str(response) if response is not None
                    else ''
                )
                logger.info(f"✅ ChatGPT応答受信: {response_content[:100]}...")
                logger.debug(f"ChatGPT応答全文:\n{response_content}")
                
            except Exception as chatgpt_error:
                log_exception(logger, chatgpt_error, "ChatGPT呼び出し")
                # エラーメッセージをメッセージに追加
                ai_response = {
                    'role': 'assistant',
                    'provider': 'chatgpt',
                    'content': f'ChatGPT呼び出し中にエラーが発生しました: {str(chatgpt_error)}',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'note'
                }
                structure["messages"].append(ai_response)
                return jsonify({
                    "success": False,
                    "error": f"ChatGPT呼び出しに失敗しました: {str(chatgpt_error)}"
                }), 500
            
            # ChatGPT出力の妥当性確認
            if not response_content.strip():
                logger.warning("ChatGPT構成出力が空です。Claude評価をスキップします。")
                # エラーメッセージをメッセージに追加
                ai_response = {
                    'role': 'assistant',
                    'provider': 'chatgpt',
                    'content': '構成が生成されませんでした。もう一度お試しください。',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'note'
                }
                structure["messages"].append(ai_response)
                logger.info("⚠️ 空の応答に対するエラーメッセージを追加")
                return jsonify({
                    "success": False,
                    "message": "構成が生成されなかったため、評価は実行されませんでした。"
                })
            
            # ChatGPTの応答をメッセージに追加
            ai_response = {
                'role': 'assistant',
                'provider': 'chatgpt',
                'content': response_content,
                'timestamp': datetime.now().isoformat(),
                'type': 'raw'
            }
            structure["messages"].append(ai_response)
            logger.info("✅ ChatGPT応答をメッセージに追加")
            
            # ChatGPT出力をログファイルに保存
            try:
                import os
                from datetime import datetime
                
                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                chatgpt_output_dir = os.path.join(log_dir, "chatgpt_output")
                if not os.path.exists(chatgpt_output_dir):
                    os.makedirs(chatgpt_output_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                chatgpt_output_file = os.path.join(chatgpt_output_dir, f"chatgpt_output_{timestamp}.json")
                
                with open(chatgpt_output_file, "w", encoding="utf-8") as f:
                    import json
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "structure_id": structure_id,
                        "user_message": user_message,
                        "chatgpt_response": response_content,
                        "response_length": len(response_content)
                    }, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ ChatGPT出力をログファイルに保存: {chatgpt_output_file}")
                
            except Exception as log_error:
                logger.warning(f"⚠️ ChatGPT出力ログ保存に失敗: {str(log_error)}")
            
            # ChatGPT応答から構成データを抽出して更新
            try:
                extracted_content = extract_json_part(response_content)
                logger.info(f"🔍 抽出された構成データ: {type(extracted_content)}")
                logger.debug(f"🔍 抽出された構成データ内容: {extracted_content}")
                
                # 抽出されたデータの妥当性確認
                if extracted_content and isinstance(extracted_content, dict):
                    # 空の辞書や無効なデータのチェック
                    if not extracted_content or extracted_content == {}:
                        logger.warning("⚠️ ChatGPT応答から空の構成データが抽出されました")
                        structure["messages"].append(
                            create_message_param(
                                role="system",
                                content="⚠️ ChatGPT応答から有効な構成データが抽出されませんでした。",
                                type="note"
                            )
                        )
                    else:
                        # 構成データを更新
                        structure["content"] = extracted_content
                        logger.info("✅ 構成データを更新しました")
                else:
                    logger.warning("⚠️ ChatGPT応答から有効な構成データが抽出されませんでした")
                    structure["messages"].append(
                        create_message_param(
                            role="system",
                            content="⚠️ ChatGPT応答から有効な構成データが抽出されませんでした。",
                            type="note"
                        )
                    )
                    
            except Exception as extract_error:
                log_exception(logger, extract_error, "構成データ抽出")
                structure["messages"].append(
                    create_message_param(
                        role="system",
                        content=f"⚠️ 構成データの抽出中にエラーが発生しました: {str(extract_error)}",
                        type="note"
                    )
                )
            
            # 構造を保存
            try:
                logger.debug("💾 構造データ保存開始")
                structure_dict = dict_to_structure_dict(structure, structure_id)
                save_structure(structure_id, structure_dict)
                logger.info("✅ 構造データ保存完了")
            except Exception as save_error:
                log_exception(logger, save_error, "構造データ保存")
                logger.error(f"❌ 構造データ保存エラー: {str(save_error)}")
            
            logger.info("✅ 会話メッセージ処理完了")
            return jsonify({
                "success": True,
                "message": "メッセージが正常に処理されました"
            })
            
        except Exception as chat_error:
            log_exception(logger, chat_error, "チャット処理")
            # エラーメッセージをメッセージに追加
            structure["messages"].append(
                create_message_param(
                    role="system",
                    content=f"⚠️ チャット処理中にエラーが発生しました: {str(chat_error)}",
                    type="note"
                )
            )
            return jsonify({
                "success": False,
                "error": f"チャット処理中にエラーが発生しました: {str(chat_error)}"
            }), 500
        
    except Exception as e:
        log_exception(logger, e, f"会話メッセージ送信 - structure_id: {structure_id}")
        return jsonify({"error": f"会話メッセージ送信中にエラーが発生しました: {str(e)}"}), 500

@unified_bp.route('/<structure_id>/save', methods=['POST'])
def save_structure_unified(structure_id):
    """
    統合インターフェースから構成を保存するAPI
    
    Args:
        structure_id: 構成のID
        
    Returns:
        Response: 保存結果のJSON
    """
    logger.info(f"💾 統合インターフェース保存開始 - structure_id: {structure_id}")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "保存データがありません"}), 400
        
        # 構成データを読み込み
        structure = load_structure_by_id(structure_id)
        if not structure:
            logger.warning(f"❌ 構成が見つかりません - structure_id: {structure_id}")
            return jsonify({"error": "構成が見つかりません"}), 404
        
        # 更新データを適用
        structure.update(data)
        
        # 構成を保存
        save_structure(structure_id, structure)  # type: ignore
        logger.info(f"✅ 統合インターフェース保存完了 - structure_id: {structure_id}")
        
        # 履歴を保存
        content_str = json.dumps(data, ensure_ascii=False, indent=2)
        save_structure_history(
            structure_id=structure_id,
            role="user",
            source="unified_interface_save",
            content=content_str,
            module_id=structure.get("module_id", "")
        )
        
        return jsonify({
            "success": True,
            "message": "構成が正常に保存されました"
        })
        
    except Exception as e:
        logger.exception(f"❌ 統合インターフェース保存中にエラーが発生 - structure_id: {structure_id}, error: {str(e)}")
        return jsonify({"error": f"保存中にエラーが発生しました: {str(e)}"}), 500

@unified_bp.route('/<structure_id>/history')
def get_structure_history(structure_id):
    """
    構成の履歴を取得するAPI
    
    Args:
        structure_id: 構成のID
        
    Returns:
        Response: 履歴データのJSON
    """
    logger.info(f"📋 構成履歴取得 - structure_id: {structure_id}")
    
    try:
        # 構成データを読み込み
        structure = load_structure_by_id(structure_id)
        if not structure:
            logger.warning(f"❌ 構成が見つかりません - structure_id: {structure_id}")
            return jsonify({"error": "構成が見つかりません"}), 404
        
        # 履歴データを取得
        history = structure.get('history', [])
        
        # 最新の10件を返す
        recent_history = history[-10:] if history else []
        
        logger.info(f"✅ 履歴取得完了 - structure_id: {structure_id}, 履歴数: {len(recent_history)}")
        
        return jsonify({
            "success": True,
            "history": recent_history
        })
        
    except Exception as e:
        logger.exception(f"❌ 履歴取得中にエラーが発生 - structure_id: {structure_id}, error: {str(e)}")
        return jsonify({"error": f"履歴取得中にエラーが発生しました: {str(e)}"}), 500

@unified_bp.route('/test-chat-message')
def test_chat_message():
    """
    チャットメッセージ送信テスト用ページ
    
    Returns:
        Response: テストページ
    """
    logger.info("🧪 チャットメッセージ送信テストページアクセス")
    
    return render_template('test_chat_message.html') 