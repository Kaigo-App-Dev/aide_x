"""
統合ルート

このモジュールは、AIDE-Xの統合インターフェース用のルートを提供します。
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import json
import os
from typing import Dict, Any, List, Optional, cast, Sequence, TypedDict, Literal, Union
import logging
import traceback
from datetime import datetime, timedelta
import uuid
import threading

from src.structure.utils import load_structure_by_id, save_structure, StructureDict, is_ui_ready
from src.structure.diff_utils import generate_diff_html
from src.llm.prompts.manager import PromptManager, PromptNotFoundError
from src.llm.prompts.prompt import Prompt
from src.exceptions import PromptNotFoundError
from src.utils.files import extract_json_part
from src.llm.providers.base import ChatMessage
from src.llm.controller import controller
from src.types import safe_cast_message_param, safe_cast_dict, safe_cast_str
from src.structure.evaluator import evaluate_structure_with
from src.structure.feedback import call_gemini_ui_generator
from src.structure.history_manager import load_evaluation_completion_history, load_structure_history, save_evaluation_completion_history, save_structure_history
from src.common.logging_utils import log_exception, log_request


# ロガーの取得
logger = logging.getLogger("unified_routes")

class ExtendedStructureDict(TypedDict):
    """拡張された構造データ型"""
    id: str
    title: str
    description: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    history: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]

MessageParam = TypedDict('MessageParam', {
    'role': str,
    'content': str,
    'name': Optional[str],
    'type': Optional[str],
    'timestamp': Optional[str],
    'source': Optional[str]
})

unified_bp = Blueprint('unified', __name__, url_prefix='/unified')

def chat_message_to_dict(message: ChatMessage) -> Dict[str, str]:
    """ChatMessageをDict[str, str]に変換する"""
    return {
        "role": message.role,
        "content": message.content,
        "timestamp": getattr(message, 'timestamp', datetime.now().isoformat())
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

def _is_placeholder_response(response: str) -> bool:
    """
    ChatGPTの応答が仮応答（placeholder）かどうかを判定する
    
    Args:
        response: ChatGPTの応答文字列
        
    Returns:
        bool: 仮応答の場合True
    """
    if not response or not isinstance(response, str):
        return True
    
    # 仮応答のパターンをチェック
    placeholder_patterns = [
        "placeholder",
        "gemini response placeholder",
        "temp response",
        "dummy response",
        "test response",
        "sample response",
        "mock response",
        "仮応答",
        "テスト応答",
        "サンプル応答"
    ]
    
    response_lower = response.lower().strip()
    
    for pattern in placeholder_patterns:
        if pattern in response_lower:
            return True
    
    # 非常に短い応答（10文字未満）も仮応答として扱う
    if len(response_lower) < 10:
        return True
    
    return False

def _is_structure_json(content: str) -> bool:
    """
    コンテンツが構成JSONかどうかを判定する
    
    Args:
        content: 判定対象のコンテンツ
        
    Returns:
        bool: 構成JSONの場合True
    """
    if not content or not isinstance(content, str):
        return False
    
    # コードブロック（```json）で囲まれているかチェック
    if "```json" in content and "```" in content:
        return True
    
    # JSONオブジェクトの開始と終了をチェック
    if content.strip().startswith("{") and content.strip().endswith("}"):
        try:
            # JSONとしてパースできるかチェック
            parsed = json.loads(content.strip())
            # titleとcontentフィールドが存在するかチェック
            if isinstance(parsed, dict) and "title" in parsed and "content" in parsed:
                return True
        except (json.JSONDecodeError, TypeError):
            pass
    
    return False

def create_message_param(
    role: str,
    content: str,
    name: Optional[str] = None,
    type: Optional[str] = None,
    timestamp: Optional[str] = None,
    source: Optional[str] = None
) -> MessageParam:
    """メッセージパラメータを作成する"""
    param = {
        "role": role,
        "content": content,
        "timestamp": timestamp or datetime.now().isoformat()
    }
    if name is not None:
        param["name"] = name
    if source is not None:
        param["source"] = source
    
    # 構成JSONの場合はtypeを"structure"に設定
    if _is_structure_json(content):
        param["type"] = "structure"
        logger.info("🔍 構成JSONを検出 - typeを'structure'に設定")
    elif type is not None:
        param["type"] = type
    
    return param

def _retry_structure_generation(original_message: str, failed_response: str) -> Optional[str]:
    """
    JSON抽出失敗時にChatGPTに対して再プロンプトを送る
    
    Args:
        original_message: 元のユーザーメッセージ
        failed_response: 失敗したChatGPT応答
        
    Returns:
        Optional[str]: 再プロンプト応答（失敗時はNone）
    """
    try:
        logger.info("🔄 再プロンプト開始")
        
        # 再プロンプト用のメッセージを作成
        retry_prompt = f"""前回の応答でJSON形式での構成生成に失敗しました。

元の要求: {original_message}

前回の応答（失敗）: {failed_response[:500]}...

**重要**: 必ず以下のJSON形式で構成を出力してください。自然文での説明は一切含めないでください。

```json
{{
  "title": "構成タイトル",
  "description": "構成の説明（任意）",
  "content": {{
    "セクション名": {{
      "項目": "内容"
    }}
  }}
}}
```

**出力ルール**:
1. 必ずJSON形式のみで出力
2. 自然文での説明は一切含めない
3. コードブロック（```json）で囲む
4. titleとcontentは必須フィールド

必ず上記のJSON形式で出力してください。"""
        
        # ChatGPTに再プロンプトを送信
        retry_messages = [
            {"role": "user", "content": retry_prompt}
        ]
        
        retry_response_dict = controller.call(
            provider="chatgpt",
            messages=retry_messages,
            model="gpt-3.5-turbo"
        )
        
        retry_response_content = retry_response_dict.get('content', '') if isinstance(retry_response_dict, dict) else ''
        if not retry_response_content and isinstance(retry_response_dict, str):
            retry_response_content = retry_response_dict
            
        if retry_response_content:
            logger.info("✅ 再プロンプト成功")
            return retry_response_content
        else:
            logger.warning("⚠️ 再プロンプト応答が空です")
            return None
            
    except Exception as e:
        logger.error(f"❌ 再プロンプトエラー: {str(e)}")
        return None

def apply_gemini_completion(structure: Dict[str, Any]):
    """
    Gemini補完を実行し、結果をstructure["completions"]に保存する
    予防機能付きで構文エラーを抑制し、成功率を向上させる
    """
    logger.info(f"🔁 Gemini補完処理を呼び出します")
    logger.info(f"📋 structure内容確認: {list(structure.keys())}")
    logger.info(f"📋 structure['messages']の数: {len(structure.get('messages', []))}")
    
    # 初期化
    if "completions" not in structure:
        structure["completions"] = []
    
    try:
        # 既存のcontrollerインスタンスを利用
        from src.llm.controller import controller
        
        # 1. Claude評価の取得と分析
        claude_evaluation = None
        if "evaluations" in structure and structure["evaluations"]:
            latest_evaluation = structure["evaluations"][-1]
            if latest_evaluation.get("status") == "success":
                claude_evaluation = latest_evaluation.get("content", "")
                logger.info(f"✅ Claude評価を取得: {claude_evaluation[:100]}...")
            else:
                logger.warning("⚠️ Claude評価のステータスがsuccessではありません")
        else:
            logger.warning("⚠️ structure['evaluations']が存在しないか空です")
        
        # 2. 元の構成内容の取得
        original_content = structure.get("content", {})
        if not original_content:
            logger.warning("⚠️ structure['content']が空です")
            original_content = {}
        
        logger.info(f"📋 元の構成内容: {type(original_content)} - キー数: {len(original_content) if isinstance(original_content, dict) else 0}")
        
        # 3. Claudeフィードバックの準備
        claude_feedback = claude_evaluation if claude_evaluation else "Claude評価が利用できません"
        logger.info(f"📋 Claudeフィードバック準備完了: {claude_feedback[:100]}...")
        
        # 4. 最適化されたプロンプトの作成
        optimized_prompt = f"""
以下の構成を基に、より詳細で実装可能な構成に補完してください。

元の構成:
{json.dumps(original_content, ensure_ascii=False, indent=2)}

Claude評価フィードバック:
{claude_feedback}

補完の要件:
1. 元の構成の意図を保持する
2. より具体的で実装可能な内容に拡張する
3. モジュール構造を明確にする
4. 各セクションの詳細を充実させる

補完結果は以下のJSON形式で返してください:
{{
  "title": "構成タイトル",
  "description": "構成の説明",
  "modules": {{
    "module1": {{
      "title": "モジュール1のタイトル",
      "description": "モジュール1の説明",
      "sections": {{
        "section1": {{
          "title": "セクション1のタイトル",
          "content": "セクション1の詳細内容",
          "implementation": "実装のポイント"
        }}
      }}
    }}
  }}
}}
"""
        logger.info(f"📤 最適化されたプロンプト作成完了: {len(optimized_prompt)}文字")
        
        # 5. Gemini補完の実行
        max_retries = 2
        retry_count = 0
        gemini_response = None
        validation_result = None
        
        while retry_count <= max_retries:
            try:
                logger.info(f"🔄 Gemini補完実行 (試行 {retry_count + 1}/{max_retries + 1})")
                
                # Gemini補完実行（プロンプトテンプレートを使用）
                try:
                    # プロンプトテンプレートを取得
                    logger.debug(f"🔍 gemini.completionプロンプトテンプレート取得開始")
                    gemini_prompt = controller.prompt_manager.get_prompt("gemini", "completion")
                    
                    if gemini_prompt:
                        logger.debug("✅ gemini.completionプロンプトテンプレート取得成功")
                        logger.debug(f"📝 プロンプトテンプレート内容: {gemini_prompt.template[:200]}...")
                        
                        gemini_provider = controller.get_provider("gemini")
                        if gemini_provider:
                            logger.debug("✅ Geminiプロバイダー取得成功")
                            
                            # APIキーの確認
                            api_key = os.getenv("GEMINI_API_KEY")
                            logger.info(f"🔐 APIキー確認: {'設定済み' if api_key else '未設定'}")
                            if api_key:
                                logger.debug(f"🔑 APIキー長: {len(api_key)}文字")
                            
                            # プロンプトパラメータの準備
                            prompt_params = {
                                "structure": json.dumps(original_content, ensure_ascii=False, indent=2),
                                "claude_feedback": claude_feedback
                            }
                            logger.debug(f"📋 プロンプトパラメータ: {list(prompt_params.keys())}")
                            logger.info(f"📤 Geminiプロンプト: {gemini_prompt.template[:200]}...")
                            
                            logger.info("📡 Gemini API送信中...")
                            gemini_response = gemini_provider.chat(
                                gemini_prompt, 
                                "gemini-1.5-flash", 
                                controller.prompt_manager,
                                **prompt_params
                            )
                            logger.info("✅ Gemini API送信完了")
                        else:
                            raise ValueError("Geminiプロバイダーの取得に失敗")
                    else:
                        logger.warning("⚠️ gemini.completionプロンプトテンプレートが見つからないため、最適化されたプロンプトを使用")
                        logger.debug(f"🔍 利用可能なプロンプト: {list(controller.prompt_manager.prompts.keys())}")
                        logger.info("📡 Gemini API送信中...")
                        gemini_response = controller.generate_response("gemini", optimized_prompt)
                        logger.info("✅ Gemini API送信完了")
                except Exception as template_error:
                    logger.warning(f"⚠️ プロンプトテンプレート使用でエラー: {template_error}")
                    logger.error(f"❌ エラータイプ: {type(template_error).__name__}")
                    import traceback
                    logger.error(f"❌ スタックトレース: {traceback.format_exc()}")
                    logger.info("🔄 最適化されたプロンプトにフォールバック")
                    logger.info("📡 Gemini API送信中...")
                    gemini_response = controller.generate_response("gemini", optimized_prompt)
                    logger.info("✅ Gemini API送信完了")
                
                if not gemini_response:
                    raise ValueError("Gemini補完応答が空です")
                
                logger.info(f"✅ Gemini補完応答取得成功 - 文字数: {len(gemini_response) if gemini_response else 0}")
                logger.debug(f"📄 Gemini生出力:")
                logger.debug(f"{'='*50}")
                logger.debug(f"{gemini_response}")
                logger.debug(f"{'='*50}")
                
                # 4. 構文チェック強化
                validation_result = validate_gemini_response_structure(gemini_response or "")
                logger.info(f"🔍 構文チェック結果: {validation_result['validation_result']}")
                
                if validation_result["validation_result"] == "valid":
                    logger.info("✅ 構文チェック成功 - 処理を続行")
                    break
                else:
                    logger.warning(f"⚠️ 構文チェック失敗: {validation_result.get('error_message', 'No message')}")
                    if retry_count < max_retries:
                        logger.info(f"🔄 リトライします (残り {max_retries - retry_count}回)")
                        retry_count += 1
                        continue
                    else:
                        logger.error("❌ 最大リトライ回数に達しました")
                        raise ValueError(f"構文チェック失敗: {validation_result.get('error_message', 'No message')}")
                        
            except Exception as e:
                logger.error(f"❌ Gemini補完実行エラー (試行 {retry_count + 1}): {str(e)}")
                logger.error(f"❌ エラータイプ: {type(e).__name__}")
                import traceback
                logger.error(f"❌ スタックトレース: {traceback.format_exc()}")
                
                # エラー詳細をログファイルに保存
                error_dump = {
                    "timestamp": datetime.now().isoformat(),
                    "structure_id": structure.get("id", "unknown"),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stack_trace": traceback.format_exc(),
                    "structure_content": original_content,
                    "claude_feedback": claude_feedback,
                    "retry_count": retry_count,
                    "max_retries": max_retries
                }
                
                # logs/claude_gemini_diff/にエラーログを保存
                os.makedirs("logs/claude_gemini_diff", exist_ok=True)
                error_log_path = f"logs/claude_gemini_diff/gemini_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{structure.get('id', 'unknown')}.json"
                with open(error_log_path, "w", encoding="utf-8") as f:
                    json.dump(error_dump, f, ensure_ascii=False, indent=2)
                logger.info(f"📝 エラーログを保存: {error_log_path}")
                
                if retry_count < max_retries:
                    logger.info(f"🔄 リトライします (残り {max_retries - retry_count}回)")
                    retry_count += 1
                    continue
                else:
                    logger.error("❌ 最大リトライ回数に達しました")
                    raise
        
        # 5. JSON抽出と処理
        try:
            extracted_json = extract_json_part(gemini_response or "")
            
            # エラーチェック
            if extracted_json and "error" in extracted_json:
                logger.warning(f"⚠️ JSON抽出でエラーが検出されました: {extracted_json['error']}")
                logger.warning(f"⚠️ エラー詳細: {extracted_json.get('reason', '不明')}")
                
                # エラー情報を含むcompletionを保存
                completion = {
                    "provider": "gemini",
                    "content": gemini_response or "",
                    "extracted_json": extracted_json,
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error_message": extracted_json['error'],
                    "error_reason": extracted_json.get('reason', '不明')
                }
                
                # 構造に補完結果を保存
                structure["completions"].append(completion)
                
                # 統計を記録
                record_gemini_completion_stats(
                    structure.get("id", "unknown"),
                    "error",
                    extracted_json['error']
                )
                
                logger.error("❌ JSON抽出エラーのため、Gemini補完を中止")
                return {
                    "status": "error",
                    "error_message": extracted_json['error'],
                    "error_reason": extracted_json.get('reason', '不明')
                }
            
            if extracted_json:
                # JSONが正常に抽出できた場合
                logger.info("✅ JSON抽出成功")
                
                # 最終的な構造検証
                final_validation = validate_gemini_response_structure(json.dumps(extracted_json))
                
                completion = {
                    "provider": "gemini",
                    "content": gemini_response or "",
                    "extracted_json": extracted_json,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "validation_result": final_validation
                }
                
                # 構造に補完結果を保存
                structure["completions"].append(completion)
                
                # Gemini補完結果を構成本体にマージ
                try:
                    logger.info("🔄 Gemini補完結果を構成本体にマージ開始")
                    
                    # 構成項目をマージ
                    if "modules" in extracted_json:
                        structure["modules"] = extracted_json["modules"]
                        logger.info("✅ modulesを構成に反映")
                    
                    if "title" in extracted_json:
                        structure["title"] = extracted_json["title"]
                        logger.info("✅ titleを構成に反映")
                    
                    if "description" in extracted_json:
                        structure["description"] = extracted_json["description"]
                        logger.info("✅ descriptionを構成に反映")
                    
                    # その他の構成項目も反映
                    for key in ["content", "metadata", "config", "settings"]:
                        if key in extracted_json:
                            structure[key] = extracted_json[key]
                            logger.info(f"✅ {key}を構成に反映")
                    
                    # 構成を保存
                    save_structure(structure["id"], cast(StructureDict, structure))
                    logger.info("💾 更新された構成を保存")
                    
                except Exception as merge_error:
                    logger.error(f"❌ 構成マージエラー: {merge_error}")
                    completion["merge_error"] = str(merge_error)
                
                # 統計を記録
                record_gemini_completion_stats(
                    structure.get("id", "unknown"),
                    "success"
                )
                
                logger.info("✅ Gemini補完処理完了")
                return {
                    "status": "success",
                    "content": gemini_response,
                    "extracted_json": extracted_json
                }
            else:
                logger.warning("⚠️ JSON抽出に失敗しました")
                raise ValueError("JSON抽出に失敗しました")
                
        except Exception as json_error:
            logger.error(f"❌ JSON処理エラー: {str(json_error)}")
            logger.error(f"❌ エラータイプ: {type(json_error).__name__}")
            import traceback
            logger.error(f"❌ スタックトレース: {traceback.format_exc()}")
            
            # エラー詳細をログファイルに保存
            error_dump = {
                "timestamp": datetime.now().isoformat(),
                "structure_id": structure.get("id", "unknown"),
                "error_type": type(json_error).__name__,
                "error_message": str(json_error),
                "stack_trace": traceback.format_exc(),
                "gemini_response": gemini_response,
                "original_content": original_content
            }
            
            # logs/claude_gemini_diff/にエラーログを保存
            os.makedirs("logs/claude_gemini_diff", exist_ok=True)
            error_log_path = f"logs/claude_gemini_diff/gemini_json_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{structure.get('id', 'unknown')}.json"
            with open(error_log_path, "w", encoding="utf-8") as f:
                json.dump(error_dump, f, ensure_ascii=False, indent=2)
            logger.info(f"📝 JSONエラーログを保存: {error_log_path}")
            
            raise
            
    except Exception as e:
        logger.error(f"❌ Gemini補完処理全体エラー: {str(e)}")
        logger.error(f"❌ エラータイプ: {type(e).__name__}")
        import traceback
        logger.error(f"❌ スタックトレース: {traceback.format_exc()}")
        
        # 統計を記録
        record_gemini_completion_stats(
            structure.get("id", "unknown"),
            "error",
            str(e)
        )
        
        return {
            "status": "error",
            "error_message": str(e),
            "error_type": type(e).__name__
        }

def _evaluate_and_append_message(structure: Dict[str, Any]) -> None:
    """Claude評価を実行し、結果をメッセージとして追加"""
    try:
        # 構成の妥当性チェック
        content = structure.get("content", {})
        if not content or (isinstance(content, dict) and not content):
            logger.warning("⚠️ 構成が空のため、Claude評価をスキップします")
            structure["evaluation"] = {
                "provider": "claude",
                "status": "skipped",
                "reason": "構成が空のため評価をスキップしました",
                "timestamp": datetime.now().isoformat()
            }
            structure["messages"].append(
                create_message_param(
                    role="system",
                    content="⚠️ 構成が空のため、Claude評価をスキップしました。構成を生成してから再評価してください。",
                    type="note",
                    source="system"
                )
            )
            return
        
        # エラー構成のチェック
        if isinstance(content, dict) and "error" in content:
            logger.warning(f"⚠️ エラー構成のため、Claude評価をスキップします: {content['error']}")
            structure["evaluation"] = {
                "provider": "claude",
                "status": "skipped",
                "reason": f"構成にエラーがあるため評価をスキップしました: {content['error']}",
                "timestamp": datetime.now().isoformat()
            }
            structure["messages"].append(
                create_message_param(
                    role="system",
                    content=f"⚠️ 構成にエラーがあるため、Claude評価をスキップしました: {content['error']}",
                    type="note",
                    source="system"
                )
            )
            return
        
        logger.info(f"🔍 Claude評価開始 - 構成キー数: {len(content) if isinstance(content, dict) else 'not_dict'}")
        logger.debug(f"🔍 評価対象構成: {content}")
        
        # Claude評価を実行
        evaluation_result = evaluate_structure_with(structure, provider="claude")
        
        if evaluation_result:
            # 評価結果を構造に保存
            structure["evaluation"] = {
                "provider": "claude",
                "status": "success",
                "score": getattr(evaluation_result, 'score', 'N/A'),
                "feedback": getattr(evaluation_result, 'feedback', 'フィードバックはありません。'),
                "details": getattr(evaluation_result, 'details', {}),
                "timestamp": datetime.now().isoformat()
            }
            
            # 評価メッセージを追加
            structure["messages"].append(
                create_message_param(
                    role="assistant",
                    content=f"🔍 **Claude評価結果**\n\nスコア: {structure['evaluation']['score']}\nフィードバック: {structure['evaluation']['feedback']}",
                    type="evaluation",
                    source="claude"
                )
            )
            logger.info(f"✅ Claude評価完了 - スコア: {structure['evaluation']['score']}")
        else:
            logger.warning("⚠️ Claude評価結果が空です")
            structure["evaluation"] = {
                "provider": "claude",
                "status": "failed",
                "reason": "評価結果が空でした",
                "timestamp": datetime.now().isoformat()
            }
            structure["messages"].append(
                create_message_param(
                    role="system",
                    content="❌ Claudeによる構成評価に失敗しました。しばらくして再試行してください。",
                    type="note",
                    source="system"
                )
            )
        
    except Exception as e:
        logger.error(f"❌ Claude評価エラー: {e}")
        structure["evaluation"] = {
            "provider": "claude",
            "status": "failed",
            "reason": f"評価中にエラーが発生しました: {str(e)}",
            "error_details": str(e),
            "timestamp": datetime.now().isoformat()
        }
        structure["messages"].append(
            create_message_param(
                role="system",
                content=f"❌ Claudeによる構成評価に失敗しました。しばらくして再試行してください。\n\nエラー詳細: {str(e)}",
                type="note",
                source="system"
            )
        )

def _apply_gemini_completion_auto(structure: Dict[str, Any]) -> None:
    """Gemini補完を自動実行し、結果を保存"""
    try:
        # Gemini補完を実行
        completion_result = call_gemini_ui_generator(structure.get("content", {}))
        
        if completion_result:
            # 補完結果を構造に保存
            structure["gemini_output"] = {
                "provider": "gemini",
                "status": "success",
                "content": completion_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Gemini補完結果をJSONとして解析し、構成に反映
            try:
                import json
                from src.utils.files import extract_json_part
                
                # JSON部分を抽出（既に辞書として返される）
                gemini_output_dict = extract_json_part(completion_result)
                if gemini_output_dict and "error" not in gemini_output_dict:
                    logger.info(f"🔍 Gemini補完結果をJSONとして解析: {list(gemini_output_dict.keys())}")
                    
                    # 構成項目をマージ
                    if "modules" in gemini_output_dict:
                        structure["modules"] = gemini_output_dict["modules"]
                        logger.info("✅ modulesを構成に反映")
                    
                    if "title" in gemini_output_dict:
                        structure["title"] = gemini_output_dict["title"]
                        logger.info("✅ titleを構成に反映")
                    
                    if "description" in gemini_output_dict:
                        structure["description"] = gemini_output_dict["description"]
                        logger.info("✅ descriptionを構成に反映")
                    
                    # その他の構成項目も反映
                    for key in ["content", "metadata", "config", "settings"]:
                        if key in gemini_output_dict:
                            structure[key] = gemini_output_dict[key]
                            logger.info(f"✅ {key}を構成に反映")
                    
                    # 構成を保存
                    save_structure(structure["id"], cast(StructureDict, structure))
                    logger.info("💾 更新された構成を保存")
                    
                else:
                    logger.warning("⚠️ Gemini補完結果からJSONを抽出できませんでした")
                    if gemini_output_dict and "error" in gemini_output_dict:
                        logger.warning(f"JSON抽出エラー: {gemini_output_dict['error']}")
                    
            except Exception as merge_error:
                logger.error(f"❌ 構成マージエラー: {merge_error}")
                structure["gemini_output"]["merge_error"] = str(merge_error)
            
            # 補完メッセージを追加
            structure["messages"].append(
                create_message_param(
                    role="assistant",
                    content=f"✨ **Gemini補完完了**\n\n{completion_result}",
                    type="completion",
                    source="gemini"
                )
            )
            logger.info("✅ Gemini補完完了")
        else:
            logger.warning("⚠️ Gemini補完結果が空です")
            structure["gemini_output"] = {
                "provider": "gemini",
                "status": "failed",
                "reason": "補完結果が空でした",
                "timestamp": datetime.now().isoformat()
            }
            structure["messages"].append(
                create_message_param(
                    role="system",
                    content="⚠️ Geminiによる補完結果が取得できませんでした。",
                    type="note",
                    source="system"
                )
            )
        
    except Exception as e:
        logger.error(f"❌ Gemini補完エラー: {e}")
        structure["gemini_output"] = {
            "provider": "gemini",
            "status": "failed",
            "reason": f"補完中にエラーが発生しました: {str(e)}",
            "error_details": str(e),
            "timestamp": datetime.now().isoformat()
        }
        structure["messages"].append(
            create_message_param(
                role="system",
                content=f"⚠️ Geminiによる補完結果が取得できませんでした。\n\nエラー詳細: {str(e)}",
                type="note",
                source="system"
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
    
    # 新規構成の場合の処理
    if structure_id == "new":
        return render_template(
            "structure/new_structure_welcome.html",
            structure_id=structure_id
        )
    
    structure = load_structure_by_id(structure_id)
    if not structure:
        return render_template("errors/404.html", message="構成が見つかりません"), 404
    
    logger.info("📂 構成データ読み込み開始 - structure_id: %s", structure_id)
    # messagesがNoneの場合は空リストに
    if structure.get('messages') is None:
        structure['messages'] = []
    logger.info("✅ 構成データ読み込み成功")
    
    error_message = None
    restore_index = request.args.get('restore', type=int)
    
    try:
        # 構成データの読み込み
        logger.info(f"📂 構成データ読み込み開始 - structure_id: {structure_id}")
        structure = load_structure_by_id(structure_id)
        
        if structure:
            logger.info(f"✅ 構成データ読み込み成功")
            # メッセージ履歴の初期化
            structure.setdefault("messages", [])
            
            # restoreパラメータがある場合、履歴から復元
            if restore_index is not None:
                logger.info(f"🔄 履歴復元開始 - index: {restore_index}")
                try:
                    # 履歴データを取得
                    histories = load_evaluation_completion_history(structure_id)
                    if histories and 0 <= restore_index < len(histories):
                        history_data = histories[restore_index]
                        logger.info(f"📖 履歴データ取得成功 - timestamp: {history_data.get('timestamp')}")
                        
                        # 履歴データを構造に反映
                        if history_data.get('evaluations'):
                            structure['evaluations'] = history_data['evaluations']
                        if history_data.get('completions'):
                            structure['completions'] = history_data['completions']
                        
                        # 復元情報をメッセージに追加
                        restore_message = create_message_param(
                            role="assistant",
                            content=f"履歴から復元しました (index: {restore_index}, timestamp: {history_data.get('timestamp', 'N/A')})",
                            type="note"
                        )
                        structure['messages'].append(restore_message)
                        
                        logger.info(f"✅ 履歴復元完了 - index: {restore_index}")
                    else:
                        logger.warning(f"⚠️ 指定された履歴が見つかりません - index: {restore_index}")
                        error_message = f"指定された履歴 (index: {restore_index}) が見つかりませんでした。"
                except Exception as restore_error:
                    logger.error(f"❌ 履歴復元エラー: {str(restore_error)}")
                    error_message = f"履歴の復元に失敗しました: {str(restore_error)}"
        else:
            logger.warning(f"⚠️ 構成ファイルが見つかりません: {structure_id}")
            error_message = f"構成ファイル '{structure_id}.json' が見つかりませんでした。"
            return render_template(
                "structure/unified_interface.html",
                structure_id=structure_id,
                structure=None,
                messages=[],
                evaluation=None,
                error=error_message,
                restore_index=restore_index
            ), 404

    except Exception as e:
        log_exception(logger, e, f"統合インターフェース表示処理 - structure_id: {structure_id}")
        error_message = f"サーバーエラーが発生しました: {str(e)}"
        return render_template(
            "structure/unified_interface.html",
            structure_id=structure_id,
            structure=None,
            messages=[],
            evaluation=None,
            error=error_message,
            restore_index=restore_index
        ), 500
        
    # 評価結果の取得
    evaluation = structure.get("metadata", {}).get("evaluation", {})
    
    # 状況分析と介入メッセージの生成
    if structure:
        analysis = analyze_structure_state(structure)
        intervention_message = generate_intervention_message(analysis)
        
        if intervention_message:
            # 既存の介入メッセージがない場合のみ追加
            existing_interventions = [msg for msg in structure.get('messages', []) 
                                    if msg.get('type') == 'intervention']
            if not existing_interventions:
                structure.setdefault('messages', []).append(intervention_message)
                logger.info(f"🤖 介入メッセージを追加 - タイプ: {analysis.get('intervention_type')}")
    
    logger.info("🎨 テンプレートのレンダリング開始")
    return render_template(
        "structure/unified_interface.html",
        structure_id=structure_id,
        structure=structure,
        messages=structure.get("messages", []),
        evaluation=evaluation,
        restore_index=restore_index
    )

@unified_bp.route('/<structure_id>/evaluate', methods=['POST'])
def evaluate_structure(structure_id):
    """構造を評価する（Claude/他プロバイダ対応）"""
    try:
        provider = request.args.get('provider', 'claude')
        _ = request.get_json(silent=True)  # 空bodyでもエラー防止
        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({'success': False, 'error': '構造が見つかりません'})
        # Claude評価
        if provider == 'claude':
            _evaluate_and_append_message(structure)
            # 最後のメッセージを返す
            last_msg = structure.get('messages', [])[-1] if structure.get('messages') else None
            save_structure(structure_id, cast(StructureDict, structure))
            return jsonify({'success': True, 'message': last_msg})
        else:
            return jsonify({'success': False, 'error': f'未対応のprovider: {provider}'})
    except Exception as e:
        logger.error(f"評価実行エラー: {str(e)}")
        return jsonify({'success': False, 'error': f'評価の実行に失敗しました: {str(e)}'})

@unified_bp.route('/<structure_id>/complete', methods=['POST'])
def complete_structure(structure_id):
    """Gemini補完を実行し、結果を返す"""
    try:
        provider = request.args.get('provider', 'gemini')
        _ = request.get_json(silent=True)
        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({'success': False, 'error': '構造が見つかりません'})
        if provider == 'gemini':
            from src.routes.unified_routes import apply_gemini_completion
            completion_result = apply_gemini_completion(structure)
            
            # 補完結果をメッセージとして追加
            if completion_result.get('status') == 'success':
                # 成功時
                msg = create_message_param(
                    role="assistant",
                    content=f"Gemini補完: {completion_result.get('content', '')}",
                    type="gemini_completion"
                )
                structure.setdefault('messages', []).append(msg)
                save_structure(structure_id, cast(StructureDict, structure))
                
                # Claude修復結果があればレスポンスに含める
                response_data = {'success': True, 'message': msg}
                if completion_result.get('fallback'):
                    response_data['completion'] = completion_result
                
                return jsonify(response_data)
            else:
                # エラー時
                error_msg = create_message_param(
                    role="assistant",
                    content=f"Gemini補完に失敗しました。構文エラーが検出されました。詳細ログを確認してください。",
                    type="gemini_error"
                )
                structure.setdefault('messages', []).append(error_msg)
                save_structure(structure_id, cast(StructureDict, structure))
                
                # Claude修復結果があればレスポンスに含める
                response_data = {
                    'success': False, 
                    'error': 'Gemini補完に失敗しました。構文エラーが検出されました。',
                    'error_details': {
                        'error_message': completion_result.get('error_message', ''),
                        'error_log_path': completion_result.get('error_log_path', ''),
                        'structure_id': structure_id
                    },
                    'message': error_msg
                }
                if completion_result.get('fallback'):
                    response_data['completion'] = completion_result
                
                return jsonify(response_data)
        else:
            return jsonify({'success': False, 'error': f'未対応のprovider: {provider}'})
    except Exception as e:
        logger.error(f"Gemini補完エラー: {str(e)}")
        return jsonify({'success': False, 'error': f'Gemini補完の実行に失敗しました: {str(e)}'})

@unified_bp.route('/<structure_id>/evaluation-history')
def get_evaluation_history(structure_id):
    """評価履歴を取得する"""
    try:
        # 履歴データを読み込み
        history_data = load_structure_history(structure_id)
        
        if not history_data:
            return jsonify({
                'success': True,
                'history': []
            })
        
        # 評価関連の履歴のみを抽出
        evaluation_history = []
        for entry in history_data.get('history', []):
            if entry.get('source') == 'structure_evaluation':
                try:
                    content_data = json.loads(entry.get('content', '{}'))
                    evaluation_history.append({
                        'provider': entry.get('role', 'unknown'),
                        'score': content_data.get('score', 0.0),
                        'feedback': content_data.get('content', ''),
                        'details': content_data.get('details', {}),
                        'timestamp': entry.get('timestamp', '')
                    })
                except json.JSONDecodeError:
                    # JSON解析に失敗した場合はスキップ
                    continue
        
        # 新しい順にソート
        evaluation_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'history': evaluation_history
        })
        
    except Exception as e:
        logger.error(f"評価履歴取得エラー: {str(e)}")
        return jsonify({'success': False, 'error': f'評価履歴の取得に失敗しました: {str(e)}'})

@unified_bp.route('/<structure_id>/chat', methods=['POST'])
def send_message(structure_id: str):
    """
    会話メッセージを送信し、AI応答と構成生成・評価を実行するAPI
    """
    try:
        log_request(logger, request, f"send_message - structure_id: {structure_id}")
        logger.info(f"💬 会話メッセージ送信開始 - structure_id: {structure_id}")

        data = request.get_json()
        if not data:
            logger.error("❌ メッセージデータがありません")
            return jsonify({"error": "メッセージデータがありません"}), 400

        message_data = data.get('message')
        if isinstance(message_data, dict):
             message_param = safe_cast_message_param(message_data)
        elif isinstance(message_data, str):
            message_param = create_message_param(role='user', content=message_data, source='chat')
        else:
            return jsonify({"error": "Invalid message format"}), 400

        if not message_param or not message_param.get('content'):
            return jsonify({"error": "メッセージが空です"}), 400
        
        message_content = message_param['content']
        source = message_param.get('source', 'chat')

        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({"error": "構成が見つかりません"}), 404

        structure.setdefault("messages", []).append(message_param)

        # ユーザーメッセージの場合はtypeを明示的に設定
        if message_param.get('role') == 'user' and not message_param.get('type'):
            message_param['type'] = 'user'
            logger.info("👤 ユーザーメッセージにtype='user'を設定しました")

        content_changed = False
        
        is_new_structure = structure.get("title") in ["新規構成", "Untitled Structure"]
        
        # 新規構成の場合は構成生成を強制実行
        if source == "chat" and is_new_structure:
            logger.info("🆕 新規チャットからの初回メッセージ、構成化プロンプトを適用します")
            try:
                prompt_manager = PromptManager()
                prompt_template_str = prompt_manager.get("structure_from_input")
                if not isinstance(prompt_template_str, str):
                    raise PromptNotFoundError("", "structure_from_input")
                
                formatted_input = prompt_template_str.format(user_input=message_content)
                logger.info("📨 structure化プロンプト使用: structure_from_input")
                logger.info(f"🧠 入力: {formatted_input[:500]}...")

                ai_response_dict = controller.call("chatgpt", [{"role": "user", "content": formatted_input}])
                raw_response = ai_response_dict.get('content', '') if isinstance(ai_response_dict, dict) else str(ai_response_dict)
                
                # ChatGPTの応答が仮応答かどうかをチェック
                if _is_placeholder_response(raw_response):
                    logger.warning("⚠️ ChatGPTが仮応答を返しました。Claude評価とGemini補完をスキップします。")
                    logger.warning(f"仮応答内容: {raw_response[:200]}...")
                    
                    # エラーメッセージをChat欄に表示
                    error_message = "申し訳ございません。構成案の生成に失敗しました。もう一度、具体的な要件をお聞かせください。"
                    structure["messages"].append(create_message_param(
                        role="assistant",
                        content=error_message,
                        source="chatgpt",
                        type="assistant_reply"
                    ))
                    
                    # 構成生成をスキップ
                    save_structure(structure_id, cast(StructureDict, structure))
                    return jsonify({
                        "success": True,
                        "messages": structure.get("messages", []),
                        "content": structure.get("content", {}),
                        "content_changed": False,
                        "error": "ChatGPT仮応答のため構成生成をスキップ"
                    })
                
                extracted_json = extract_json_part(raw_response)
                
                if extracted_json:
                    logger.info("✅ 応答から構成JSONの抽出に成功しました")
                    natural_language_part = raw_response.split("```json")[0].strip()
                    ai_response_content = natural_language_part if natural_language_part else "構成案を作成しました。ご確認ください。"
                    
                    structure["title"] = extracted_json.get("title", structure["title"])
                    structure["description"] = extracted_json.get("description", structure["description"])
                    structure["content"] = extracted_json.get("content", structure["content"])
                    structure["metadata"]["updated_at"] = datetime.utcnow().isoformat()
                    content_changed = True

                    # ChatGPTの自然な返答（会話）
                    structure["messages"].append(create_message_param(
                        role="assistant",
                        content=ai_response_content,
                        source="chatgpt",
                        type="assistant_reply"
                    ))

                    # Claudeによる構成評価（構成案カードとして）
                    try:
                        check_prompt_template = prompt_manager.get("claude_check_structure")
                        if isinstance(check_prompt_template, str):
                            claude_prompt = check_prompt_template.format(
                                structure_json=json.dumps(extracted_json, ensure_ascii=False, indent=2)
                            )
                            logger.info("🤖 Claudeへの確認プロンプトを生成しました")
                            
                            claude_response_dict = controller.call("claude", [{"role": "user", "content": claude_prompt}])
                            claude_response_content = claude_response_dict.get('content', '') if isinstance(claude_response_dict, dict) else str(claude_response_dict)

                            if claude_response_content:
                                # Claude評価結果はstructureに保存し、chat欄には通知のみ
                                structure["claude_evaluation"] = {
                                    "content": claude_response_content,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "status": "success"
                                }
                                
                                # chat欄には通知メッセージのみを追加
                                structure["messages"].append(create_message_param(
                                    role="assistant",
                                    content="🔍 Claude評価を実行しました。中央ペインに評価結果を表示しています。",
                                    source="claude",
                                    type="notification"
                                ))
                                logger.info("✅ Claude評価完了通知をメッセージに追加しました")
                                
                                # 確認メッセージは削除して一連の流れを自動化
                                logger.info("✅ 構成生成と評価が完了しました。Gemini補完を自動実行します。")
                                
                                # Gemini補完を自動実行
                                try:
                                    logger.info("🔁 Gemini補完処理を呼び出します")
                                    logger.info(f"📋 現在のstructure内容: {list(structure.keys())}")
                                    logger.info(f"📋 structure['messages']の数: {len(structure.get('messages', []))}")
                                    
                                    # 最新のstructure_proposalメッセージを確認
                                    structure_messages = structure.get('messages', [])
                                    latest_structure_proposal = None
                                    for msg in reversed(structure_messages):
                                        if msg.get('type') == 'structure_proposal':
                                            latest_structure_proposal = msg
                                            break
                                    
                                    if latest_structure_proposal:
                                        logger.info(f"✅ 最新のstructure_proposalを発見: {latest_structure_proposal.get('content', '')[:100]}...")
                                    else:
                                        logger.warning("⚠️ structure_proposalメッセージが見つかりません")
                                    
                                    completion_result = apply_gemini_completion(structure)
                                    
                                    logger.info(f"📤 Gemini補完結果: {completion_result.get('status', 'unknown')}")
                                    
                                    # Gemini補完結果をメッセージに追加
                                    if completion_result.get("status") == "success":
                                        logger.info("✅ Gemini補完が成功しました")
                                        
                                        # chat欄には通知メッセージのみを追加
                                        structure["messages"].append(create_message_param(
                                            role="assistant",
                                            content="✨ Gemini補完が完了しました。右ペインに構成を表示しています。",
                                            source="gemini",
                                            type="notification"
                                        ))
                                        logger.info("✅ Gemini補完完了通知をメッセージに追加しました")
                                        
                                        # structure["modules"]が更新されているか確認
                                        if "modules" in structure:
                                            logger.info(f"✅ structure['modules']が更新されました - モジュール数: {len(structure['modules'])}")
                                        else:
                                            logger.warning("⚠️ structure['modules']が更新されていません")
                                            
                                    else:
                                        logger.warning("⚠️ Gemini補完が失敗しました")
                                        error_message = completion_result.get("error_message", "不明なエラー")
                                        logger.error(f"❌ Gemini補完エラー詳細: {error_message}")
                                        
                                        # エラー通知メッセージを追加
                                        structure["messages"].append(create_message_param(
                                            role="assistant",
                                            content="⚠️ Gemini補完に失敗しました。構成は正常に生成されています。",
                                            source="gemini",
                                            type="notification"
                                        ))
                                        
                                        # フォールバックがある場合は通知のみ追加
                                        if completion_result.get("fallback"):
                                            structure["messages"].append(create_message_param(
                                                role="assistant",
                                                content="🔄 Claudeによる修復を試行しました。",
                                                source="claude",
                                                type="notification"
                                            ))
                                            logger.info("✅ Claude修復通知をメッセージに追加しました")
                                        
                                except Exception as gemini_error:
                                    logger.error(f"❌ Gemini補完実行エラー: {str(gemini_error)}")
                                    logger.error(f"❌ エラータイプ: {type(gemini_error).__name__}")
                                    import traceback
                                    logger.error(f"❌ スタックトレース: {traceback.format_exc()}")
                                    
                                    # エラー通知メッセージを追加
                                    structure["messages"].append(create_message_param(
                                        role="assistant",
                                        content="❌ Gemini補完の実行中にエラーが発生しました。構成は正常に生成されています。",
                                        source="system",
                                        type="notification"
                                    ))
                        else:
                            logger.warning("⚠️ Claudeからの応答が空でした。")
                            # Claude評価失敗時のメッセージを追加
                            structure["messages"].append(create_message_param(
                                role="assistant",
                                content="Claudeによる構成評価に失敗しました。構成は正常に生成されています。",
                                source="claude",
                                type="structure_proposal"
                            ))
                        if not isinstance(check_prompt_template, str):
                            logger.warning("⚠️ claude_check_structureプロンプトが見つからないか、不正な形式です")
                            # プロンプトが見つからない場合のメッセージを追加
                            structure["messages"].append(create_message_param(
                                role="assistant",
                                content="Claudeによる構成評価の設定に問題があります。構成は正常に生成されています。",
                                source="claude",
                                type="structure_proposal"
                            ))

                    except PromptNotFoundError as e:
                        log_exception(logger, e, "claude_check_structureプロンプトの取得に失敗")
                        # プロンプト取得失敗時のメッセージを追加
                        structure["messages"].append(create_message_param(
                            role="assistant",
                            content="Claudeによる構成評価の設定に問題があります。構成は正常に生成されています。",
                            source="claude",
                            type="structure_proposal"
                        ))
                    except Exception as claude_error:
                        log_exception(logger, claude_error, "Claude呼び出し中にエラーが発生しました")
                        # Claude呼び出しエラー時のメッセージを追加
                        structure["messages"].append(create_message_param(
                            role="assistant",
                            content="Claudeによる構成評価中にエラーが発生しました。構成は正常に生成されています。",
                            source="claude",
                            type="structure_proposal"
                        ))

                else:
                    logger.warning("⚠️ 応答から構成JSONを抽出できませんでした。再プロンプトで構成生成を強制します。")
                    
                    # 再プロンプトで構成生成を強制
                    retry_prompt = f"""前回の応答でJSON形式での構成生成に失敗しました。

元の要求: {message_content}

**重要**: 必ず以下のJSON形式で構成を出力してください。自然文での説明は一切含めないでください。

```json
{{
  "title": "構成タイトル",
  "description": "構成の説明（任意）",
  "content": {{
    "セクション名": {{
      "項目": "内容"
    }}
  }}
}}
```

**出力ルール**:
1. 必ずJSON形式のみで出力
2. 自然文での説明は一切含めない
3. コードブロック（```json）で囲む
4. titleとcontentは必須フィールド

必ず上記のJSON形式で出力してください。"""
                    
                    # ChatGPTに再プロンプトを送信
                    retry_messages = [
                        {"role": "user", "content": retry_prompt}
                    ]
                    
                    retry_response_dict = controller.call("chatgpt", messages=retry_messages)
                    retry_raw_response = retry_response_dict.get('content', '') if isinstance(retry_response_dict, dict) else str(retry_response_dict)
                    
                    # 再プロンプトでも仮応答チェック
                    if _is_placeholder_response(retry_raw_response):
                        logger.warning("⚠️ 再プロンプトでもChatGPTが仮応答を返しました。")
                        logger.warning(f"再プロンプト仮応答内容: {retry_raw_response[:200]}...")
                        
                        # エラーメッセージをChat欄に表示
                        error_message = "申し訳ございません。構成案の生成に失敗しました。もう一度、具体的な要件をお聞かせください。"
                        structure["messages"].append(create_message_param(
                            role="assistant",
                            content=error_message,
                            source="chatgpt",
                            type="assistant_reply"
                        ))
                        
                        # 構成生成をスキップ
                        save_structure(structure_id, cast(StructureDict, structure))
                        return jsonify({
                            "success": True,
                            "messages": structure.get("messages", []),
                            "content": structure.get("content", {}),
                            "content_changed": False,
                            "error": "再プロンプトでもChatGPT仮応答のため構成生成をスキップ"
                        })
                    
                    retry_extracted_json = extract_json_part(retry_raw_response)
                    
                    if retry_extracted_json:
                        logger.info("✅ 再プロンプトで構成JSONの抽出に成功しました")
                        
                        structure["title"] = retry_extracted_json.get("title", structure["title"])
                        structure["description"] = retry_extracted_json.get("description", structure["description"])
                        structure["content"] = retry_extracted_json.get("content", structure["content"])
                        structure["metadata"]["updated_at"] = datetime.utcnow().isoformat()
                        content_changed = True

                        # ChatGPTの自然な返答（会話）
                        structure["messages"].append(create_message_param(
                            role="assistant",
                            content="構成案を作成しました。ご確認ください。",
                            source="chatgpt",
                            type="assistant_reply"
                        ))

                        # Claudeによる構成評価（構成案カードとして）
                        try:
                            check_prompt_template = prompt_manager.get("claude_check_structure")
                            if isinstance(check_prompt_template, str):
                                claude_prompt = check_prompt_template.format(
                                    structure_json=json.dumps(retry_extracted_json, ensure_ascii=False, indent=2)
                                )
                                logger.info("🤖 Claudeへの確認プロンプトを生成しました")
                                
                                claude_response_dict = controller.call("claude", [{"role": "user", "content": claude_prompt}])
                                claude_response_content = claude_response_dict.get('content', '') if isinstance(claude_response_dict, dict) else str(claude_response_dict)

                                if claude_response_content:
                                    # Claude評価結果はstructureに保存し、chat欄には通知のみ
                                    structure["claude_evaluation"] = {
                                        "content": claude_response_content,
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "status": "success"
                                    }
                                    
                                    # chat欄には通知メッセージのみを追加
                                    structure["messages"].append(create_message_param(
                                        role="assistant",
                                        content="🔍 Claude評価を実行しました。中央ペインに評価結果を表示しています。",
                                        source="claude",
                                        type="notification"
                                    ))
                                    logger.info("✅ Claude評価完了通知をメッセージに追加しました")
                                    
                                    # 確認メッセージは削除して一連の流れを自動化
                                    logger.info("✅ 構成生成と評価が完了しました。Gemini補完を自動実行します。")
                                    
                                    # Gemini補完を自動実行
                                    try:
                                        logger.info("🔁 Gemini補完処理を呼び出します")
                                        logger.info(f"📋 現在のstructure内容: {list(structure.keys())}")
                                        logger.info(f"📋 structure['messages']の数: {len(structure.get('messages', []))}")
                                        
                                        # 最新のstructure_proposalメッセージを確認
                                        structure_messages = structure.get('messages', [])
                                        latest_structure_proposal = None
                                        for msg in reversed(structure_messages):
                                            if msg.get('type') == 'structure_proposal':
                                                latest_structure_proposal = msg
                                                break
                                        
                                        if latest_structure_proposal:
                                            logger.info(f"✅ 最新のstructure_proposalを発見: {latest_structure_proposal.get('content', '')[:100]}...")
                                        else:
                                            logger.warning("⚠️ structure_proposalメッセージが見つかりません")
                                        
                                        completion_result = apply_gemini_completion(structure)
                                        
                                        logger.info(f"📤 Gemini補完結果: {completion_result.get('status', 'unknown')}")
                                        
                                        # Gemini補完結果をメッセージに追加
                                        if completion_result.get("status") == "success":
                                            logger.info("✅ Gemini補完が成功しました")
                                            
                                            # chat欄には通知メッセージのみを追加
                                            structure["messages"].append(create_message_param(
                                                role="assistant",
                                                content="✨ Gemini補完が完了しました。右ペインに構成を表示しています。",
                                                source="gemini",
                                                type="notification"
                                            ))
                                            logger.info("✅ Gemini補完完了通知をメッセージに追加しました")
                                            
                                            # structure["modules"]が更新されているか確認
                                            if "modules" in structure:
                                                logger.info(f"✅ structure['modules']が更新されました - モジュール数: {len(structure['modules'])}")
                                            else:
                                                logger.warning("⚠️ structure['modules']が更新されていません")
                                                
                                        else:
                                            logger.warning("⚠️ Gemini補完が失敗しました")
                                            error_message = completion_result.get("error_message", "不明なエラー")
                                            logger.error(f"❌ Gemini補完エラー詳細: {error_message}")
                                            
                                            # エラー通知メッセージを追加
                                            structure["messages"].append(create_message_param(
                                                role="assistant",
                                                content="⚠️ Gemini補完に失敗しました。構成は正常に生成されています。",
                                                source="gemini",
                                                type="notification"
                                            ))
                                            
                                            # フォールバックがある場合は通知のみ追加
                                            if completion_result.get("fallback"):
                                                structure["messages"].append(create_message_param(
                                                    role="assistant",
                                                    content="🔄 Claudeによる修復を試行しました。",
                                                    source="claude",
                                                    type="notification"
                                                ))
                                                logger.info("✅ Claude修復通知をメッセージに追加しました")
                                    except Exception as gemini_error:
                                        logger.error(f"❌ Gemini補完実行エラー: {str(gemini_error)}")
                                        logger.error(f"❌ エラータイプ: {type(gemini_error).__name__}")
                                        import traceback
                                        logger.error(f"❌ スタックトレース: {traceback.format_exc()}")
                                        
                                        # エラー通知メッセージを追加
                                        structure["messages"].append(create_message_param(
                                            role="assistant",
                                            content="❌ Gemini補完の実行中にエラーが発生しました。構成は正常に生成されています。",
                                            source="system",
                                            type="notification"
                                        ))
                                else:
                                    logger.warning("⚠️ Claudeからの応答が空でした。")
                                    # Claude評価失敗時の通知メッセージを追加
                                    structure["messages"].append(create_message_param(
                                        role="assistant",
                                        content="⚠️ Claude評価に失敗しました。構成は正常に生成されています。",
                                        source="claude",
                                        type="notification"
                                    ))
                                if not isinstance(check_prompt_template, str):
                                    logger.warning("⚠️ claude_check_structureプロンプトが見つからないか、不正な形式です")
                                    # プロンプトが見つからない場合の通知メッセージを追加
                                    structure["messages"].append(create_message_param(
                                        role="assistant",
                                        content="⚠️ Claude評価の設定に問題があります。構成は正常に生成されています。",
                                        source="claude",
                                        type="notification"
                                    ))

                        except PromptNotFoundError as e:
                            log_exception(logger, e, "claude_check_structureプロンプトの取得に失敗")
                            # プロンプト取得失敗時の通知メッセージを追加
                            structure["messages"].append(create_message_param(
                                role="assistant",
                                content="⚠️ Claude評価の設定に問題があります。構成は正常に生成されています。",
                                source="claude",
                                type="notification"
                            ))
                        except Exception as claude_error:
                            log_exception(logger, claude_error, "Claude呼び出し中にエラーが発生しました")
                            # Claude呼び出しエラー時の通知メッセージを追加
                            structure["messages"].append(create_message_param(
                                role="assistant",
                                content="⚠️ Claude評価中にエラーが発生しました。構成は正常に生成されています。",
                                source="claude",
                                type="notification"
                            ))
                    
                    else:
                        logger.error("❌ 再プロンプトでも構成JSONの抽出に失敗しました。エラーメッセージを表示します。")
                        error_message = "申し訳ございません。構成の生成に失敗しました。もう一度、具体的な要件をお聞かせください。"
                        structure["messages"].append(create_message_param(
                            role="assistant", 
                            content=error_message, 
                            source="chatgpt",
                            type="assistant_reply"
                        ))

            except (PromptNotFoundError, Exception) as e:
                log_exception(logger, e, "構成化プロンプト処理中にエラーが発生しました")
                ai_response_content = "申し訳ありません、構成の生成中にエラーが発生しました。"
                structure["messages"].append(create_message_param(
                    role="system", 
                    content=ai_response_content, 
                    type="error"
                ))
        
        else:
            logger.info("💬 通常の会話フローを実行します")
            
            MAX_HISTORY_MESSAGES = 10
            recent_messages_params = structure.get("messages", [])[-MAX_HISTORY_MESSAGES:]
            chat_history = [message_param_to_chat_message(m) for m in recent_messages_params]
            api_messages = [chat_message_to_dict(m) for m in chat_history]

            ai_response_dict = controller.call("chatgpt", messages=api_messages)
            ai_response_content = ai_response_dict.get('content', '') if isinstance(ai_response_dict, dict) else str(ai_response_dict)
            
            if not ai_response_content:
                ai_response_content = "申し訳ございませんが、応答を生成できませんでした。"
            
            structure["messages"].append(create_message_param(
                role="assistant", 
                content=ai_response_content, 
                source="chatgpt",
                type="assistant_reply"
            ))

        save_structure(structure_id, cast(StructureDict, structure))
        logger.info(f"✅ メッセージ送信処理完了 - structure_id: {structure_id}")

        # Gemini補完の結果を確認
        gemini_completion_result = None
        if "completions" in structure and structure["completions"]:
            latest_completion = structure["completions"][-1]
            if latest_completion.get("provider") == "gemini":
                gemini_completion_result = {
                    "status": latest_completion.get("status", "unknown"),
                    "content": latest_completion.get("content", ""),
                    "error_message": latest_completion.get("error_message", "")
                }
                logger.info(f"📤 Gemini補完結果をレスポンスに含めます: {gemini_completion_result['status']}")

        # 最新のstructure全体を返す（modules、title、descriptionを含む）
        response_data = {
            "success": True,
            "messages": structure.get("messages", []),
            "structure": structure,  # 最新のstructure全体
            "content": structure.get("content", {}),
            "modules": structure.get("modules", {}),  # modulesを明示的に含める
            "title": structure.get("title", ""),
            "description": structure.get("description", ""),
            "content_changed": content_changed,
            "gemini_completion": gemini_completion_result
        }
        
        logger.info(f"📤 レスポンス送信 - modules数: {len(structure.get('modules', {}))}")
        logger.info(f"📤 レスポンス送信 - title: {structure.get('title', 'N/A')}")
        
        return jsonify(response_data)

    except Exception as e:
        log_exception(logger, e, f"会話メッセージ送信 - structure_id: {structure_id}")
        return jsonify({"success": False, "error": "サーバー内部で予期せぬエラーが発生しました。"}), 500

def generate_evaluation_html(evaluation_result: Dict[str, Any]) -> str:
    """
    評価結果をHTML形式で生成する
    
    Args:
        evaluation_result: 評価結果辞書
        
    Returns:
        str: HTML形式の評価結果
    """
    if not evaluation_result:
        return '<div class="evaluation-empty">評価結果がありません</div>'
    
    html_parts = []
    
    # スコア表示
    if evaluation_result.get("score"):
        score = evaluation_result["score"]
        score_percentage = int(score * 100) if isinstance(score, (int, float)) else "N/A"
        html_parts.append(f'''
        <div class="evaluation-score">
            <div class="score-item">
                <div class="score-value">{score_percentage}</div>
                <div class="score-label">総合評価</div>
            </div>
        </div>
        ''')
    
    # フィードバック表示
    if evaluation_result.get("feedback"):
        html_parts.append(f'''
        <div class="evaluation-feedback">
            {evaluation_result["feedback"]}
        </div>
        ''')
    
    # 詳細情報表示
    details = evaluation_result.get("details", {})
    if details:
        # 強み・弱みの表示
        if details.get("strengths"):
            html_parts.append(f'''
            <div class="evaluation-suggestions">
                <strong>✅ 強み:</strong>
                <p>{details["strengths"]}</p>
            </div>
            ''')
        
        if details.get("weaknesses"):
            html_parts.append(f'''
            <div class="evaluation-suggestions">
                <strong>⚠️ 改善点:</strong>
                <p>{details["weaknesses"]}</p>
            </div>
            ''')
        
        # 改善提案の表示
        if details.get("suggestions"):
            html_parts.append(f'''
            <div class="evaluation-suggestions">
                <strong>💡 改善提案:</strong>
                <ul>
                    {''.join([f'<li>{suggestion}</li>' for suggestion in details["suggestions"]])}
                </ul>
            </div>
            ''')
    
    if not html_parts:
        return '<div class="evaluation-empty">評価結果がありません</div>'
    
    return ''.join(html_parts)

def generate_improved_structure(structure: Dict[str, Any], suggestions: List[str]) -> Optional[Dict[str, Any]]:
    """
    Claude評価のsuggestionsを基にGeminiで改善構成を生成する
    
    Args:
        structure: 元の構成データ
        suggestions: Claude評価からの改善提案リスト
        
    Returns:
        Optional[Dict[str, Any]]: 改善された構成データ（失敗時はNone）
    """
    try:
        logger.info(f"✨ Gemini改善構成生成開始 - suggestions数: {len(suggestions)}")
        
        if not suggestions:
            logger.warning("⚠️ 改善提案が空のため、Gemini改善構成をスキップ")
            return None
        
        # 元の構成データを準備
        original_content = structure.get("content", {})
        original_title = structure.get("title", "無題")
        original_description = structure.get("description", "")
        
        # Geminiへのプロンプト作成
        suggestions_text = "\n".join([f"- {suggestion}" for suggestion in suggestions])
        
        prompt = f"""
以下の構成に対して、Claude評価からの改善提案を基に、より良い構成を生成してください。

## 元の構成
**タイトル**: {original_title}
**説明**: {original_description}
**構成内容**:
{json.dumps(original_content, ensure_ascii=False, indent=2)}

## Claude評価からの改善提案
{suggestions_text}

## 要求事項
1. 上記の改善提案を踏まえて、構成を改善してください
2. 元の構成の良い部分は保持しつつ、改善提案を反映してください
3. 有効なJSON形式で返してください
4. タイトル、説明、contentを含む完全な構成を返してください

## 返却形式
以下のJSON形式で返してください：
{{
  "title": "改善されたタイトル",
  "description": "改善された説明",
  "content": {{
    // 改善された構成内容
  }}
}}
"""
        
        # Geminiに改善構成を依頼
        from src.llm.controller import controller
        gemini_response = controller.generate_response("gemini", prompt)
        
        if not gemini_response or not gemini_response.strip():
            logger.warning("⚠️ Gemini応答が空でした")
            return None
        
        # JSON部分を抽出
        extracted_json = extract_json_part(gemini_response)
        if not extracted_json:
            logger.warning("⚠️ Gemini応答から有効なJSONを抽出できませんでした")
            return None
        
        # 改善構成の検証
        if not isinstance(extracted_json, dict):
            logger.warning("⚠️ 抽出されたJSONが辞書形式ではありません")
            return None
        
        # 必須フィールドの確認
        if not extracted_json.get("content"):
            logger.warning("⚠️ 改善構成にcontentフィールドがありません")
            return None
        
        # 改善構成にメタデータを追加
        improved_structure = {
            "id": f"{structure.get('id', 'unknown')}_improved_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": extracted_json.get("title", f"{original_title} (改善版)"),
            "description": extracted_json.get("description", original_description),
            "content": extracted_json.get("content", {}),
            "metadata": {
                "original_structure_id": structure.get("id"),
                "improvement_timestamp": datetime.now().isoformat(),
                "claude_suggestions": suggestions,
                "provider": "gemini",
                "type": "improved_structure"
            }
        }
        
        logger.info(f"✅ Gemini改善構成生成完了 - タイトル: {improved_structure['title']}")
        return improved_structure
        
    except Exception as e:
        log_exception(logger, e, "Gemini改善構成生成")
        return None

@unified_bp.route('/unified/<structure_id>/evaluate-improved', methods=['POST'])
def evaluate_improved_structure(structure_id):
    """改善構成をClaudeで評価する"""
    try:
        data = request.get_json()
        improved_structure = data.get('improved_structure')
        
        if not improved_structure:
            return jsonify({'success': False, 'error': '改善構成データがありません'})
        
        logger.info(f"🔍 改善構成評価開始 - structure_id: {structure_id}")
        
        # 改善構成を評価
        evaluation_result = evaluate_structure_with_claude(improved_structure)
        
        if not evaluation_result:
            return jsonify({'success': False, 'error': '評価に失敗しました'})
        
        # 評価結果をHTML形式で生成
        evaluation_html = generate_evaluation_html(evaluation_result)
        
        # 評価履歴に保存
        save_evaluation_to_history(structure_id, evaluation_result, "improved_structure")
        
        logger.info(f"✅ 改善構成評価完了 - スコア: {evaluation_result.get('score', 'N/A')}")
        
        return jsonify({
            'success': True,
            'evaluation_html': evaluation_html,
            'evaluation_result': evaluation_result
        })
        
    except Exception as e:
        log_exception(logger, e, "改善構成評価")
        return jsonify({'success': False, 'error': str(e)})

@unified_bp.route('/unified/<structure_id>/compare-structures', methods=['POST'])
def compare_structures(structure_id):
    """元の構成と改善構成の差分を生成する"""
    try:
        data = request.get_json()
        original_structure = data.get('original_structure')
        improved_structure = data.get('improved_structure')
        
        if not original_structure or not improved_structure:
            return jsonify({'success': False, 'error': '構成データが不足しています'})
        
        logger.info(f"🔍 構成差分生成開始 - structure_id: {structure_id}")
        
        # 差分を生成
        diff_result = generate_structure_diff(original_structure, improved_structure)
        
        if not diff_result:
            return jsonify({'success': False, 'error': '差分生成に失敗しました'})
        
        # 差分をHTML形式で生成
        diff_html = generate_diff_html(diff_result)
        
        logger.info(f"✅ 構成差分生成完了")
        
        return jsonify({
            'success': True,
            'diff_html': diff_html,
            'diff_result': diff_result
        })
        
    except Exception as e:
        log_exception(logger, e, "構成差分生成")
        return jsonify({'success': False, 'error': str(e)})

def generate_diff_html(diff_result):
    """差分結果をHTML形式で生成"""
    try:
        html_parts = []
        
        # 差分サマリー
        if diff_result.get('summary'):
            html_parts.append(f"""
                <div class="diff-summary" style="background: rgba(78, 201, 176, 0.1); border-left: 4px solid #4ec9b0; padding: 15px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
                    <h4 style="color: #4ec9b0; margin: 0 0 10px 0;">📊 差分サマリー</h4>
                    <p style="margin: 0; color: #cccccc;">{diff_result['summary']}</p>
                </div>
            """)
        
        # 詳細差分
        if diff_result.get('details'):
            html_parts.append('<div class="diff-details">')
            html_parts.append('<h4 style="color: #4ec9b0; margin: 0 0 15px 0;">🔍 詳細差分</h4>')
            
            for detail in diff_result['details']:
                change_type = detail.get('type', 'unknown')
                field = detail.get('field', 'unknown')
                old_value = detail.get('old_value', '')
                new_value = detail.get('new_value', '')
                
                # 変更タイプに応じたスタイル
                if change_type == 'added':
                    style_class = 'added'
                    icon = '➕'
                    title = '追加'
                elif change_type == 'removed':
                    style_class = 'removed'
                    icon = '➖'
                    title = '削除'
                elif change_type == 'modified':
                    style_class = 'changed'
                    icon = '🔄'
                    title = '変更'
                else:
                    style_class = 'unchanged'
                    icon = '📝'
                    title = 'その他'
                
                html_parts.append(f"""
                    <div class="diff-item {style_class}" style="background: rgba(78, 201, 176, 0.05); border: 1px solid rgba(78, 201, 176, 0.2); border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                        <div class="diff-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                            <span style="font-size: 16px;">{icon}</span>
                            <strong style="color: #4ec9b0;">{title}</strong>
                            <span style="color: #cccccc;">- {field}</span>
                        </div>
                        <div class="diff-content">
                            {f'<div class="diff-line removed" style="background: rgba(220, 53, 69, 0.1); color: #dc3545; padding: 8px; border-radius: 4px; margin-bottom: 5px;"><strong>削除:</strong> {old_value}</div>' if old_value else ''}
                            {f'<div class="diff-line added" style="background: rgba(40, 167, 69, 0.1); color: #28a745; padding: 8px; border-radius: 4px;"><strong>追加:</strong> {new_value}</div>' if new_value else ''}
                        </div>
                    </div>
                """)
            
            html_parts.append('</div>')
        
        # 統計情報
        if diff_result.get('statistics'):
            stats = diff_result['statistics']
            html_parts.append(f"""
                <div class="diff-statistics" style="background: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107; padding: 15px; margin-top: 20px; border-radius: 0 8px 8px 0;">
                    <h4 style="color: #ffc107; margin: 0 0 10px 0;">📈 変更統計</h4>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div><strong>追加:</strong> <span style="color: #28a745;">{stats.get('added', 0)}</span></div>
                        <div><strong>削除:</strong> <span style="color: #dc3545;">{stats.get('removed', 0)}</span></div>
                        <div><strong>変更:</strong> <span style="color: #ffc107;">{stats.get('modified', 0)}</span></div>
                        <div><strong>変更なし:</strong> <span style="color: #6c757d;">{stats.get('unchanged', 0)}</span></div>
                    </div>
                </div>
            """)
        
        return ''.join(html_parts)
        
    except Exception as e:
        log_exception(logger, e, "差分HTML生成")
        return f'<div style="color: #dc3545;">差分表示エラー: {str(e)}</div>'

def generate_random_structure_id() -> str:
    """ランダムな構成IDを生成する"""
    return str(uuid.uuid4())

def create_blank_structure(structure_id: str) -> Dict[str, Any]:
    """空の構成ファイルを作成する"""
    blank_structure = {
        "id": structure_id,
        "title": "新規構成",
        "description": "新しく作成された構成です",
        "content": {},
        "metadata": {
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        },
        "history": [],
        "messages": [
            {
                "role": "assistant",
                "content": "こんにちは！新しい構成を作成しましょう。何を作りたいですか？",
                "type": "assistant",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "chat"
            }
        ],
        "evaluations": {}
    }
    
    # ファイルに保存
    save_structure(structure_id, cast(StructureDict, blank_structure))
    logger.info(f"✅ 新規構成を作成しました - structure_id: {structure_id}")
    
    return blank_structure

@unified_bp.route("/new")
def new_unified_structure():
    """新規構成作成画面"""
    try:
        new_id = generate_random_structure_id()
        create_blank_structure(new_id)
        logger.info(f"🆕 新規構成作成 - structure_id: {new_id}")
        return redirect(url_for("unified.unified_interface", structure_id=new_id))
    except Exception as e:
        logger.error(f"❌ 新規構成作成エラー: {str(e)}")
        return render_template("errors/500.html", message="新規構成の作成に失敗しました"), 500

@unified_bp.route('/structure/<structure_id>/evaluation_history')
def evaluation_history_page(structure_id):
    """評価履歴ページを表示"""
    logger.info(f"📊 評価履歴ページ表示開始 - structure_id: {structure_id}")
    
    try:
        structure = load_structure_by_id(structure_id)
        if not structure:
            return render_template("errors/404.html", message="構成が見つかりません"), 404
        
        # 評価履歴を取得
        evaluations = structure.get('evaluations', [])
        logger.info(f"✅ 評価履歴取得成功 - 件数: {len(evaluations)}")
        
        return render_template(
            'structure/evaluation_history.html',
            structure=structure,
            structure_id=structure_id,
            evaluations=evaluations
        )
        
    except Exception as e:
        log_exception(logger, e, f"評価履歴ページ表示処理 - structure_id: {structure_id}")
        return render_template("errors/500.html", message="評価履歴の取得に失敗しました"), 500

@unified_bp.route('/structure/<structure_id>/completion_history')
def completion_history_page(structure_id):
    """補完履歴ページを表示"""
    logger.info(f"🔁 補完履歴ページ表示開始 - structure_id: {structure_id}")
    
    try:
        structure = load_structure_by_id(structure_id)
        if not structure:
            return render_template("errors/404.html", message="構成が見つかりません"), 404
        
        # 補完履歴を取得
        completions = structure.get('completions', [])
        logger.info(f"✅ 補完履歴取得成功 - 件数: {len(completions)}")
        
        return render_template(
            'structure/completion_history.html',
            structure=structure,
            structure_id=structure_id,
            completions=completions
        )
        
    except Exception as e:
        log_exception(logger, e, f"補完履歴ページ表示処理 - structure_id: {structure_id}")
        return render_template("errors/500.html", message="補完履歴の取得に失敗しました"), 500

def prepare_prompt_for_structure(user_input: str) -> str:
    """
    ユーザーの入力から構成生成用のプロンプト文を自動生成
    
    Args:
        user_input: ユーザーの入力メッセージ
        
    Returns:
        str: 構成生成用のプロンプト
    """
    return f"""ユーザーの要望に基づいて、実用的な構成JSONを生成してください。
構成が不十分な場合は、ユーザーの意図を理解して自動的に補完してください。

**ユーザーの入力**: 「{user_input}」

**出力形式**: 必ず以下のJSON形式で出力してください。自然文での説明は一切含めないでください。

```json
{{
  "title": "構成のタイトル",
  "description": "構成の目的と概要",
  "content": {{
    "対象ユーザー": "誰が使うか",
    "主要機能": {{
      "機能名": "機能の説明"
    }},
    "技術要件": {{
      "フロントエンド": "使用技術",
      "バックエンド": "使用技術",
      "データベース": "使用技術"
    }},
    "画面構成": {{
      "画面名": "画面の説明"
    }}
  }}
}}
```

**重要な指示**:
1. 必ずJSON形式のみで出力（自然文禁止）
2. コードブロック（```json）で囲む
3. title、description、contentは必須
4. ユーザーの意図を理解し、実用的な構成を提案
5. 不足している項目は適切に補完
6. 具体的で実装可能な内容にする

**禁止事項**:
- 自然文での説明
- Markdown形式での出力
- リスト形式での出力
- コードブロック外での説明

**補完方針**:
- ユーザーの入力が抽象的でも、一般的な構成パターンに基づいて補完
- 業界標準やベストプラクティスを参考にする
- 拡張性と保守性を考慮した構成にする"""

def check_structure_completeness(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    構成に必要なフィールドが揃っているかを確認
    
    Args:
        structure: 構成データ
        
    Returns:
        Dict[str, Any]: 完全性チェック結果
    """
    result = {
        "is_complete": True,
        "missing_fields": [],
        "suggestions": [],
        "score_threshold": 0.7
    }
    
    content = structure.get("content", {})
    evaluation = structure.get("evaluation", {})
    
    # 基本的な項目チェック
    if not structure.get("title"):
        result["missing_fields"].append("構成のタイトル")
        result["is_complete"] = False
    
    if not structure.get("description"):
        result["missing_fields"].append("構成の説明")
        result["suggestions"].append("目的や概要を明確にしてください")
    
    # content内の詳細チェック
    if content and isinstance(content, dict):
        # 対象ユーザーのチェック
        if not content.get("対象ユーザー") and not content.get("target_users"):
            result["missing_fields"].append("対象ユーザー")
            result["is_complete"] = False
            result["suggestions"].append("誰が使うアプリか教えてください")
        
        # 主要機能のチェック
        main_functions = content.get("主要機能") or content.get("main_functions") or content.get("機能")
        if not main_functions or (isinstance(main_functions, dict) and not main_functions):
            result["missing_fields"].append("主要機能")
            result["is_complete"] = False
            result["suggestions"].append("どんな機能が必要か教えてください")
        
        # 技術要件のチェック
        tech_requirements = content.get("技術要件") or content.get("technical_requirements")
        if not tech_requirements or (isinstance(tech_requirements, dict) and not tech_requirements):
            result["missing_fields"].append("技術要件")
            result["is_complete"] = False
            result["suggestions"].append("使用したい技術があれば教えてください")
        
        # 画面構成のチェック
        screens = content.get("画面構成") or content.get("screens") or content.get("画面")
        if not screens or (isinstance(screens, dict) and not screens):
            result["missing_fields"].append("画面構成")
            result["is_complete"] = False
            result["suggestions"].append("どんな画面が必要か教えてください")
    
    else:
        # contentが空または無効な場合
        result["missing_fields"].append("構成の詳細内容")
        result["is_complete"] = False
        result["suggestions"].append("構成の詳細を教えてください")
    
    # Claude評価スコアチェック
    if evaluation and evaluation.get("status") == "success":
        score = evaluation.get("score", 0)
        if score < result["score_threshold"]:
            result["is_complete"] = False
            result["suggestions"].append(f"評価スコアが低いです（{score}）。構成を改善してください")
        
        # 評価フィードバックから不足項目を抽出
        feedback = evaluation.get("feedback", "")
        if "不足" in feedback or "不十分" in feedback or "不明" in feedback:
            result["suggestions"].append("評価フィードバックを参考に構成を改善してください")
    
    # Gemini補完結果チェック
    gemini_output = structure.get("gemini_output", {})
    if gemini_output and gemini_output.get("status") == "success":
        content_text = gemini_output.get("content", "")
        if not content_text or len(content_text.strip()) < 50:
            result["is_complete"] = False
            result["suggestions"].append("補完結果が不十分です。より詳細な構成が必要です")
    
    return result

@unified_bp.route('/<structure_id>/auto_complete', methods=['POST'])
def auto_complete_confirmation(structure_id: str):
    """
    自動補完確認のAPIエンドポイント
    
    Args:
        structure_id: 構成のID
        
    Returns:
        JSON: 処理結果
    """
    try:
        logger.info(f"🔄 自動補完確認開始 - structure_id: {structure_id}")
        
        # JSONデータの取得
        data = request.get_json()
        if not data:
            return jsonify({"error": "データがありません"}), 400
        
        confirmation = data.get('confirmation', '').lower()
        if confirmation not in ['yes', 'no']:
            return jsonify({"error": "無効な確認値です"}), 400
        
        # 構造データを読み込み
        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({"error": "構成が見つかりません"}), 404
        
        if confirmation == 'yes':
            # 自動補完を実行
            logger.info("✅ 自動補完を実行します")
            
            # 構成完全性チェック
            completeness_check = check_structure_completeness(structure)
            missing_fields = completeness_check.get("missing_fields", [])
            
            # 自動補完を実行
            enhanced_structure = auto_complete_structure(structure, missing_fields)
            
            # 成功メッセージを追加
            enhanced_structure["messages"].append(
                create_message_param(
                    role="assistant",
                    content="✅ 構成を自動補完しました。",
                    type="completion_success",
                    source="system"
                )
            )
            
            # 構成を保存
            save_structure(structure_id, cast(StructureDict, enhanced_structure))
            
            logger.info("✅ 自動補完完了")
            return jsonify({
                "success": True,
                "message": "構成を自動補完しました",
                "structure": enhanced_structure
            })
        
        else:  # confirmation == 'no'
            # 手動補完を促すメッセージを追加
            logger.info("❌ 自動補完をキャンセルしました")
            
            completeness_check = check_structure_completeness(structure)
            missing_fields = completeness_check.get("missing_fields", [])
            suggestions = completeness_check.get("suggestions", [])
            
            # ガイダンスメッセージを生成
            guidance_message = render_guidance_message(missing_fields, suggestions)
            
            structure["messages"].append(
                create_message_param(
                    role="assistant",
                    content=guidance_message,
                    type="completion_guidance",
                    source="system"
                )
            )
            
            # 構成を保存
            save_structure(structure_id, cast(StructureDict, structure))
            
            return jsonify({
                "success": True,
                "message": "手動補完を促すメッセージを追加しました",
                "structure": structure
            })
        
    except Exception as e:
        logger.error(f"❌ 自動補完確認エラー: {e}")
        return jsonify({
            "success": False,
            "error": f"自動補完確認の処理に失敗しました: {str(e)}"
        }), 500

def render_completion_check_message(missing_fields: List[str], suggestions: List[str]) -> str:
    """
    構成完全性チェック結果に応じたYes/Noメッセージを生成
    
    Args:
        missing_fields: 不足しているフィールドのリスト
        suggestions: 改善提案のリスト
        
    Returns:
        str: HTML形式の確認メッセージ
    """
    missing_fields_text = "\n".join([f"- {field}" for field in missing_fields])
    suggestions_text = "\n".join([f"- {suggestion}" for suggestion in suggestions])
    
    return f"""⚠️ この構成には不足があります。

**不足項目:**
{missing_fields_text}

**改善提案:**
{suggestions_text}

自動補完してもよろしいですか？

<div class="completion-confirmation">
    <button class="btn btn-success" onclick="confirmCompletion('yes')">はい</button>
    <button class="btn btn-secondary" onclick="confirmCompletion('no')">いいえ</button>
</div>"""

def render_guidance_message(missing_fields: List[str], suggestions: List[str]) -> str:
    """
    「いいえ」選択時のガイダンスメッセージを生成
    
    Args:
        missing_fields: 不足しているフィールドのリスト
        suggestions: 改善提案のリスト
        
    Returns:
        str: HTML形式のガイダンスメッセージ
    """
    missing_fields_text = "\n".join([f"- {field}" for field in missing_fields])
    suggestions_text = "\n".join([f"- {suggestion}" for suggestion in suggestions])
    
    return f"""👍 OK！一緒に考えていきましょう！

今の構成には、以下の項目がまだ不明です：

{missing_fields_text}

**補完のために、教えてください！**

{suggestions_text}

💡 ヒント: 具体的に教えていただけると、より良い構成を作れます！"""

def auto_complete_structure(structure: Dict[str, Any], missing_fields: List[str]) -> Dict[str, Any]:
    """
    「はい」が押された場合、ChatGPTで構成を補完
    
    Args:
        structure: 現在の構成データ
        missing_fields: 不足しているフィールドのリスト
        
    Returns:
        Dict[str, Any]: 補完された構成データ
    """
    try:
        logger.info(f"🔄 自動補完開始 - 不足フィールド: {missing_fields}")
        
        # 現在の構成を取得
        current_content = structure.get("content", {})
        current_title = structure.get("title", "")
        current_description = structure.get("description", "")
        
        # 補完プロンプトを生成
        completion_prompt = f"""現在の構成を改善し、不足している項目を補完してください。

**現在の構成:**
タイトル: {current_title or "未設定"}
説明: {current_description or "未設定"}
内容: {json.dumps(current_content, indent=2, ensure_ascii=False)}

**不足項目:**
{chr(10).join([f"- {field}" for field in missing_fields])}

**補完要求:**
1. 不足項目を適切に補完する
2. 既存の構成を保持しつつ改善する
3. 必ずJSON形式で出力する
4. 自然文での説明は含めない
5. 実用的で具体的な内容にする

**出力形式:**
```json
{{
  "title": "改善された構成タイトル",
  "description": "改善された構成の説明",
  "content": {{
    "対象ユーザー": "具体的なユーザー像",
    "主要機能": {{
      "機能名": "機能の詳細説明"
    }},
    "技術要件": {{
      "フロントエンド": "具体的な技術",
      "バックエンド": "具体的な技術",
      "データベース": "具体的な技術"
    }},
    "画面構成": {{
      "画面名": "画面の詳細説明"
    }}
  }}
}}
```"""
        
        # ChatGPTで構成を改善
        api_messages = [
            {"role": "user", "content": completion_prompt}
        ]
        
        enhanced_response = controller.call(
            provider="chatgpt",
            messages=api_messages,
            model="gpt-3.5-turbo",
        )
        
        enhanced_content = enhanced_response.get('content', '') if isinstance(enhanced_response, dict) else enhanced_response
        
        if enhanced_content:
            # 改善された構成を抽出
            enhanced_json = extract_json_part(enhanced_content)
            if enhanced_json and "error" not in enhanced_json:
                # 構成を更新
                if "content" in enhanced_json:
                    # content部分のみをマージ
                    structure["content"].update(enhanced_json.get("content", {}))
                else:
                    # contentがない場合は全体をマージ
                    structure["content"].update(enhanced_json)

                # titleとdescriptionも更新（存在する場合）
                if enhanced_json.get("title"):
                    structure["title"] = enhanced_json["title"]
                if enhanced_json.get("description"):
                    structure["description"] = enhanced_json["description"]
                
                logger.info("✅ 自動補完完了")
                return structure
            else:
                logger.warning("⚠️ 改善された構成の抽出に失敗")
                return structure
        else:
            logger.warning("⚠️ ChatGPTからの改善応答が空")
            return structure
            
    except Exception as e:
        logger.error(f"❌ 自動補完エラー: {e}")
        return structure

@unified_bp.route('/<structure_id>/debug-messages')
def debug_messages(structure_id: str):
    """デバッグ用：メッセージ履歴を表示"""
    try:
        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({"error": "Structure not found"}), 404
        
        messages = structure.get("messages", [])
        return jsonify({
            "structure_id": structure_id,
            "message_count": len(messages),
            "messages": messages
        })
    except Exception as e:
        logger.error(f"デバッグメッセージ取得エラー: {e}")
        return jsonify({"error": str(e)}), 500

@unified_bp.route('/api/structure_content/<structure_id>')
def get_structure_content(structure_id):
    """構成内容を取得するAPIエンドポイント"""
    try:
        logger.info(f"🔍 構成内容取得リクエスト: {structure_id}")
        
        structure = load_structure_by_id(structure_id)
        if not structure:
            logger.warning(f"❌ 構成が見つかりません: {structure_id}")
            return jsonify({"error": "構成が見つかりません"}), 404
        
        logger.info(f"✅ 構成内容取得成功: {structure_id}")
        return jsonify({"structure": structure})
        
    except Exception as e:
        logger.error(f"❌ 構成内容取得エラー: {e}")
        return jsonify({"error": f"構成内容の取得に失敗しました: {str(e)}"}), 500

def record_gemini_completion_stats(structure_id: str, status: str, error_message: Optional[str] = None, additional_data: Optional[Dict[str, Any]] = None):
    """
    Gemini補完の統計情報を記録する（拡張版）
    
    Args:
        structure_id (str): 構造ID
        status (str): 補完ステータス（"success", "error", "failed", "skipped"）
        error_message (str, optional): エラーメッセージ
        additional_data (Dict[str, Any], optional): 追加データ（Claude分析結果など）
    """
    try:
        stats_file = os.path.join("logs", "gemini_completion_stats.json")
        
        # 既存の統計を読み込み
        stats = {}
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        
        # 統計を更新
        if "total_completions" not in stats:
            stats["total_completions"] = 0
        if "successful_completions" not in stats:
            stats["successful_completions"] = 0
        if "failed_completions" not in stats:
            stats["failed_completions"] = 0
        if "skipped_completions" not in stats:
            stats["skipped_completions"] = 0
        if "error_types" not in stats:
            stats["error_types"] = {}
        if "recent_errors" not in stats:
            stats["recent_errors"] = []
        if "claude_analysis_stats" not in stats:
            stats["claude_analysis_stats"] = {
                "too_long_count": 0,
                "vague_count": 0,
                "empty_count": 0,
                "normal_count": 0
            }
        if "prevention_effectiveness" not in stats:
            stats["prevention_effectiveness"] = {
                "retry_success_count": 0,
                "retry_failure_count": 0,
                "skip_prevented_errors": 0
            }
        
        stats["total_completions"] += 1
        
        if status == "success":
            stats["successful_completions"] += 1
        elif status == "skipped":
            stats["skipped_completions"] += 1
        else:
            stats["failed_completions"] += 1
            
            # エラータイプを記録
            if error_message:
                error_type = "unknown"
                if "JSON" in error_message:
                    error_type = "json_parsing"
                elif "API" in error_message:
                    error_type = "api_error"
                elif "timeout" in error_message.lower():
                    error_type = "timeout"
                elif "rate limit" in error_message.lower():
                    error_type = "rate_limit"
                elif "構文チェック失敗" in error_message:
                    error_type = "syntax_validation"
                
                if error_type not in stats["error_types"]:
                    stats["error_types"][error_type] = 0
                stats["error_types"][error_type] += 1
                
                # 最近のエラーを記録（最大10件）
                recent_error = {
                    "timestamp": datetime.now().isoformat(),
                    "structure_id": structure_id,
                    "error_type": error_type,
                    "error_message": error_message[:200] + "..." if len(error_message) > 200 else error_message
                }
                stats["recent_errors"].append(recent_error)
                if len(stats["recent_errors"]) > 10:
                    stats["recent_errors"] = stats["recent_errors"][-10:]
        
        # Claude分析統計を更新
        if additional_data and "claude_analysis" in additional_data:
            claude_analysis = additional_data["claude_analysis"]
            if claude_analysis:
                analysis_result = claude_analysis.get("analysis_result", "normal")
                if analysis_result == "too_long":
                    stats["claude_analysis_stats"]["too_long_count"] += 1
                elif analysis_result == "vague":
                    stats["claude_analysis_stats"]["vague_count"] += 1
                elif analysis_result == "empty":
                    stats["claude_analysis_stats"]["empty_count"] += 1
                else:
                    stats["claude_analysis_stats"]["normal_count"] += 1
        
        # 予防効果統計を更新
        if additional_data:
            retry_count = additional_data.get("retry_count", 0)
            if retry_count > 0 and status == "success":
                stats["prevention_effectiveness"]["retry_success_count"] += 1
            elif retry_count > 0 and status != "success":
                stats["prevention_effectiveness"]["retry_failure_count"] += 1
            
            if status == "skipped":
                stats["prevention_effectiveness"]["skip_prevented_errors"] += 1
        
        # 成功率を計算
        if stats["total_completions"] > 0:
            stats["success_rate"] = round(stats["successful_completions"] / stats["total_completions"] * 100, 2)
        
        # 予防効果率を計算
        total_attempts = stats["successful_completions"] + stats["failed_completions"]
        if total_attempts > 0:
            prevention_rate = round(
                (stats["prevention_effectiveness"]["retry_success_count"] + 
                 stats["prevention_effectiveness"]["skip_prevented_errors"]) / total_attempts * 100, 2
            )
            stats["prevention_effectiveness"]["effectiveness_rate"] = prevention_rate
        
        # 統計を保存
        os.makedirs("logs", exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
        logger.info(f"📊 Gemini補完統計を更新: {status} - 成功率: {stats.get('success_rate', 0)}% - 予防効果率: {stats.get('prevention_effectiveness', {}).get('effectiveness_rate', 0)}%")
        
    except Exception as e:
        logger.error(f"❌ Gemini補完統計記録エラー: {str(e)}")

@unified_bp.route('/gemini_completion_stats', methods=['GET'])
def get_gemini_completion_stats():
    """Gemini補完統計を取得する（拡張版）"""
    try:
        stats_file = os.path.join("logs", "gemini_completion_stats.json")
        
        if not os.path.exists(stats_file):
            return jsonify({
                "success": True,
                "stats": {
                    "total_completions": 0,
                    "successful_completions": 0,
                    "failed_completions": 0,
                    "skipped_completions": 0,
                    "success_rate": 0,
                    "error_types": {},
                    "recent_errors": [],
                    "claude_analysis_stats": {
                        "too_long_count": 0,
                        "vague_count": 0,
                        "empty_count": 0,
                        "normal_count": 0
                    },
                    "prevention_effectiveness": {
                        "retry_success_count": 0,
                        "retry_failure_count": 0,
                        "skip_prevented_errors": 0,
                        "effectiveness_rate": 0
                    }
                }
            })
        
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"❌ Gemini補完統計取得エラー: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"統計情報の取得に失敗しました: {str(e)}"
        }), 500

def analyze_claude_evaluation(claude_content: str) -> Dict[str, Any]:
    """
    Claude評価の品質を分析し、必要に応じて要約する
    
    Args:
        claude_content (str): Claude評価の内容
        
    Returns:
        Dict[str, Any]: 分析結果と要約された内容
    """
    logger.info(f"🔍 Claude評価分析開始 - 文字数: {len(claude_content)}")
    
    analysis = {
        "original_length": len(claude_content),
        "is_too_long": False,
        "is_vague": False,
        "is_empty": False,
        "should_skip": False,
        "summary": claude_content,
        "analysis_result": "normal"
    }
    
    # 空文字列チェック
    if not claude_content or not claude_content.strip():
        analysis["is_empty"] = True
        analysis["should_skip"] = True
        analysis["analysis_result"] = "empty"
        logger.warning("⚠️ Claude評価が空です")
        return analysis
    
    # 長さチェック（800文字以上）
    if len(claude_content) > 800:
        analysis["is_too_long"] = True
        analysis["analysis_result"] = "too_long"
        logger.warning(f"⚠️ Claude評価が長すぎます: {len(claude_content)}文字")
        
        # 要約を実行
        try:
            analysis["summary"] = shorten_claude_feedback(claude_content)
            logger.info(f"✅ Claude評価を要約しました: {len(analysis['summary'])}文字")
        except Exception as e:
            logger.error(f"❌ Claude評価要約に失敗: {e}")
            analysis["summary"] = claude_content[:400] + "..."
    
    # 不明瞭な内容チェック
    vague_indicators = [
        "構成が不十分です",
        "改善が必要です",
        "問題があります",
        "不適切です",
        "見直してください"
    ]
    
    is_vague = any(indicator in claude_content for indicator in vague_indicators)
    if is_vague and len(claude_content) < 100:
        analysis["is_vague"] = True
        analysis["analysis_result"] = "vague"
        logger.warning("⚠️ Claude評価が不明瞭です")
    
    # スキップ判定
    if analysis["is_empty"] or (analysis["is_vague"] and analysis["is_too_long"]):
        analysis["should_skip"] = True
        analysis["analysis_result"] = "skip"
    
    logger.info(f"✅ Claude評価分析完了: {analysis['analysis_result']}")
    return analysis

def shorten_claude_feedback(content: str) -> str:
    """
    Claude評価を要約する
    
    Args:
        content (str): 元のClaude評価
        
    Returns:
        str: 要約された評価
    """
    try:
        # 既存のcontrollerインスタンスを利用
        from src.llm.controller import controller
        
        summary_prompt = f"""
以下のClaude評価を、Gemini補完に適した形に要約してください。重要な指摘のみを抽出し、具体的で簡潔な形にしてください。

【元の評価】:
{content}

【要約ルール】:
- 重要な改善点のみを抽出
- 具体的な指摘を優先
- 抽象的な表現は避ける
- 箇条書き形式で出力
- 200文字以内に収める

要約された評価のみを返してください。
"""
        
        summary_response = controller.generate_response("claude", summary_prompt)
        if summary_response and len(summary_response) > 0:
            return summary_response.strip()
        else:
            # フォールバック: 手動で要約
            return manual_summarize_feedback(content)
            
    except Exception as e:
        logger.error(f"❌ Claude評価要約エラー: {e}")
        return manual_summarize_feedback(content)

def manual_summarize_feedback(content: str) -> str:
    """
    手動でClaude評価を要約する（フォールバック用）
    
    Args:
        content (str): 元のClaude評価
        
    Returns:
        str: 要約された評価
    """
    # 重要なキーワードを抽出
    important_keywords = [
        "不足", "不十分", "重複", "矛盾", "不明確", "改善", "追加", "修正",
        "不足している", "必要", "重要", "問題", "エラー", "不適切"
    ]
    
    lines = content.split('\n')
    important_lines = []
    
    for line in lines:
        line = line.strip()
        if any(keyword in line for keyword in important_keywords):
            if len(line) > 10:  # 短すぎる行は除外
                important_lines.append(line)
    
    if important_lines:
        summary = '\n'.join(important_lines[:5])  # 最大5行まで
        if len(summary) > 400:
            summary = summary[:400] + "..."
        return summary
    else:
        # 重要なキーワードが見つからない場合は最初の部分を使用
        return content[:300] + "..." if len(content) > 300 else content

def create_optimized_gemini_prompt(structure_content: Dict[str, Any], claude_feedback: str) -> str:
    """
    Gemini用の最適化されたプロンプトを作成する
    
    Args:
        structure_content (Dict[str, Any]): 構造の内容
        claude_feedback (str): Claude評価（要約済み）
        
    Returns:
        str: 最適化されたプロンプト
    """
    # 構造をJSON文字列に変換
    structure_json = json.dumps(structure_content, ensure_ascii=False, indent=2)
    
    # 最適化されたプロンプトテンプレート
    prompt = f"""以下の構成JSONを改善してください。改善のヒントとしてClaudeによる評価コメントを添えます。

【構成】:
{structure_json}

【Claude評価コメント】:
{claude_feedback}

この指摘を元に、構成JSON全体を再構成し、完成形を JSON形式でのみ 出力してください。

【重要】:
- JSON形式でのみ出力してください
- コードブロック（```json）は使用しないでください
- 説明文やコメントは含めないでください
- 有効なJSONオブジェクトのみを返してください
- "title"と"modules"キーは必ず含めてください

出力例:
{{
  "title": "改善された構成",
  "description": "Claude評価を反映した改善版",
  "modules": [
    {{
      "name": "モジュール名",
      "description": "モジュールの説明"
    }}
  ]
}}"""
    
    return prompt

def validate_gemini_response_structure(response: str) -> Dict[str, Any]:
    """
    Gemini応答の構造を検証する
    
    Args:
        response (str): Geminiの応答
        
    Returns:
        Dict[str, Any]: 検証結果
    """
    validation = {
        "has_title": False,
        "has_modules": False,
        "is_valid_structure": False,
        "missing_keys": [],
        "validation_result": "unknown",
        "error_message": ""
    }
    
    # 必須キーの存在チェック
    if '"title"' in response or "'title'" in response:
        validation["has_title"] = True
    
    if '"modules"' in response or "'modules'" in response:
        validation["has_modules"] = True
    
    # 不足しているキーを記録
    if not validation["has_title"]:
        validation["missing_keys"].append("title")
    
    if not validation["has_modules"]:
        validation["missing_keys"].append("modules")
    
    # 全体の妥当性判定
    if validation["has_title"] and validation["has_modules"]:
        validation["is_valid_structure"] = True
        validation["validation_result"] = "valid"
        validation["error_message"] = ""
    else:
        validation["validation_result"] = "invalid"
        missing_keys_str = ", ".join(validation["missing_keys"])
        validation["error_message"] = f"必須キーが不足しています: {missing_keys_str}"
        logger.warning(f"⚠️ Gemini応答に必須キーが不足: {validation['missing_keys']}")
    
    return validation

def analyze_structure_state(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    構成の現在の状態を分析し、介入が必要かどうかを判定する
    
    Args:
        structure: 分析対象の構成データ
        
    Returns:
        Dict[str, Any]: 分析結果
            - intervention_needed (bool): 介入が必要かどうか
            - intervention_type (str): 介入の種類
            - analysis_details (Dict): 詳細な分析結果
    """
    try:
        analysis = {
            "intervention_needed": False,
            "intervention_type": None,
            "analysis_details": {}
        }
        
        # 構成の基本チェック
        content = structure.get("content", {})
        messages = structure.get("messages", [])
        evaluation = structure.get("evaluation", {})
        
        # 1. 空の構成チェック
        if not content or (isinstance(content, dict) and not content):
            analysis["intervention_needed"] = True
            analysis["intervention_type"] = "empty_structure"
            analysis["analysis_details"]["reason"] = "構成が空です。構成生成を開始してください。"
            return analysis
        
        # 2. 評価結果のチェック
        if evaluation and evaluation.get("status") == "failed":
            analysis["intervention_needed"] = True
            analysis["intervention_type"] = "evaluation_failed"
            analysis["analysis_details"]["reason"] = "評価に失敗しました。再評価を試してください。"
            return analysis
        
        # 3. 低スコアのチェック
        if evaluation and evaluation.get("score"):
            score = float(evaluation.get("score", 0))
            if score < 0.6:
                analysis["intervention_needed"] = True
                analysis["intervention_type"] = "low_score"
                analysis["analysis_details"]["reason"] = f"評価スコアが低いです（{score:.2f}）。改善を検討してください。"
                return analysis
        
        # 4. メッセージ履歴のチェック
        if len(messages) > 10:
            analysis["intervention_needed"] = True
            analysis["intervention_type"] = "long_conversation"
            analysis["analysis_details"]["reason"] = "会話が長くなっています。構成を整理することをお勧めします。"
            return analysis
        
        # 5. エラー構成のチェック
        if isinstance(content, dict) and "error" in content:
            analysis["intervention_needed"] = True
            analysis["intervention_type"] = "error_structure"
            analysis["analysis_details"]["reason"] = f"構成にエラーがあります: {content['error']}"
            return analysis
        
        # 介入不要の場合
        analysis["analysis_details"]["reason"] = "構成は正常な状態です。"
        return analysis
        
    except Exception as e:
        logger.error(f"構成状態分析中にエラーが発生: {str(e)}")
        return {
            "intervention_needed": False,
            "intervention_type": "analysis_error",
            "analysis_details": {"reason": f"分析中にエラーが発生しました: {str(e)}"}
        }

def generate_intervention_message(analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    分析結果に基づいて介入メッセージを生成する
    
    Args:
        analysis: analyze_structure_state()の結果
        
    Returns:
        Optional[Dict[str, Any]]: 介入メッセージ、不要な場合はNone
    """
    try:
        if not analysis.get("intervention_needed", False):
            return None
        
        intervention_type = analysis.get("intervention_type")
        reason = analysis.get("analysis_details", {}).get("reason", "")
        
        # intervention_typeがNoneの場合はデフォルトメッセージを返す
        if intervention_type is None:
            return {
                "role": "system",
                "content": f"🤖 **システム介入**\n\n{reason}",
                "type": "intervention",
                "source": "system"
            }
        
        # 介入タイプに応じたメッセージを生成
        messages = {
            "empty_structure": {
                "role": "system",
                "content": f"🤖 **システム介入**\n\n{reason}\n\n構成生成を開始するには、チャットで構成の内容を説明してください。",
                "type": "intervention",
                "source": "system"
            },
            "evaluation_failed": {
                "role": "system",
                "content": f"🤖 **システム介入**\n\n{reason}\n\n評価ボタンを押して再評価を試してください。",
                "type": "intervention",
                "source": "system"
            },
            "low_score": {
                "role": "system",
                "content": f"🤖 **システム介入**\n\n{reason}\n\n構成の改善を検討してください。",
                "type": "intervention",
                "source": "system"
            },
            "long_conversation": {
                "role": "system",
                "content": f"🤖 **システム介入**\n\n{reason}\n\n新しい構成を作成するか、現在の構成を整理することをお勧めします。",
                "type": "intervention",
                "source": "system"
            },
            "error_structure": {
                "role": "system",
                "content": f"🤖 **システム介入**\n\n{reason}\n\n構成を修正するか、新しい構成を作成してください。",
                "type": "intervention",
                "source": "system"
            },
            "analysis_error": {
                "role": "system",
                "content": f"🤖 **システム介入**\n\n{reason}\n\nシステムエラーが発生しました。ページを再読み込みしてください。",
                "type": "intervention",
                "source": "system"
            }
        }
        
        return messages.get(intervention_type, {
            "role": "system",
            "content": f"🤖 **システム介入**\n\n{reason}",
            "type": "intervention",
            "source": "system"
        })
        
    except Exception as e:
        logger.error(f"介入メッセージ生成中にエラーが発生: {str(e)}")
        return None

def save_evaluation_to_history(structure_id: str, evaluation_result: Dict[str, Any], source: str = "evaluation") -> bool:
    """
    評価結果を履歴に保存する
    
    Args:
        structure_id: 構成ID
        evaluation_result: 評価結果
        source: 評価のソース（"evaluation", "improved_structure"等）
        
    Returns:
        bool: 保存成功時True、失敗時False
    """
    try:
        # 評価結果をJSON文字列に変換
        content = json.dumps(evaluation_result, ensure_ascii=False, indent=2)
        
        # 履歴に保存
        success = save_structure_history(
            structure_id=structure_id,
            role="system",
            source=source,
            content=content,
            module_id="evaluation"
        )
        
        if success:
            logger.info(f"✅ 評価履歴を保存しました - structure_id: {structure_id}, source: {source}")
        else:
            logger.warning(f"⚠️ 評価履歴の保存に失敗しました - structure_id: {structure_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 評価履歴保存中にエラーが発生: {str(e)}")
        return False

def evaluate_structure_with_claude(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Claudeを使用して改善構成を評価する
    
    Args:
        structure: 評価対象の改善構成
        
    Returns:
        Dict[str, Any]: 評価結果
    """
    try:
        # 既存のevaluate_structure_with関数を使用
        evaluation_result = evaluate_structure_with(structure, provider="claude")
        
        if evaluation_result:
            return {
                "score": getattr(evaluation_result, 'score', 0.0),
                "feedback": getattr(evaluation_result, 'feedback', '評価が完了しました'),
                "details": {
                    "strengths": "構成が改善されました",
                    "weaknesses": "さらなる改善の余地があります",
                    "suggestions": ["より詳細な実装を検討してください"]
                }
            }
        else:
            return {
                "score": 0.0,
                "feedback": "評価に失敗しました",
                "details": {
                    "strengths": "",
                    "weaknesses": "評価処理でエラーが発生しました",
                    "suggestions": ["評価を再試行してください"]
                }
            }
            
    except Exception as e:
        logger.error(f"Claude評価中にエラーが発生: {str(e)}")
        return {
            "score": 0.0,
            "feedback": f"評価中にエラーが発生しました: {str(e)}",
            "details": {
                "strengths": "",
                "weaknesses": "評価処理でエラーが発生しました",
                "suggestions": ["評価を再試行してください"]
            }
        }

def generate_structure_diff(original_structure: Dict[str, Any], improved_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    元の構成と改善構成の差分を生成する
    
    Args:
        original_structure: 元の構成
        improved_structure: 改善された構成
        
    Returns:
        Dict[str, Any]: 差分結果
    """
    try:
        diff_result = {
            "summary": "構成の差分が生成されました",
            "details": [],
            "statistics": {
                "added": 0,
                "removed": 0,
                "modified": 0,
                "unchanged": 0
            }
        }
        
        # 基本的なフィールドの差分をチェック
        fields_to_check = ["title", "description"]
        
        for field in fields_to_check:
            original_value = original_structure.get(field, "")
            improved_value = improved_structure.get(field, "")
            
            if original_value != improved_value:
                diff_result["details"].append({
                    "type": "modified",
                    "field": field,
                    "old_value": original_value,
                    "new_value": improved_value
                })
                diff_result["statistics"]["modified"] += 1
            else:
                diff_result["statistics"]["unchanged"] += 1
        
        # contentフィールドの差分をチェック
        original_content = original_structure.get("content", {})
        improved_content = improved_structure.get("content", {})
        
        if original_content != improved_content:
            diff_result["details"].append({
                "type": "modified",
                "field": "content",
                "old_value": str(original_content)[:100] + "..." if len(str(original_content)) > 100 else str(original_content),
                "new_value": str(improved_content)[:100] + "..." if len(str(improved_content)) > 100 else str(improved_content)
            })
            diff_result["statistics"]["modified"] += 1
        else:
            diff_result["statistics"]["unchanged"] += 1
        
        return diff_result
        
    except Exception as e:
        logger.error(f"差分生成中にエラーが発生: {str(e)}")
        return {
            "summary": "差分生成に失敗しました",
            "details": [],
            "statistics": {
                "added": 0,
                "removed": 0,
                "modified": 0,
                "unchanged": 0
            }
        }