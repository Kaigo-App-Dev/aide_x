# utils/generator.py

import uuid
import json
import logging
from typing import Dict, Any, Optional
from src.llm.hub import call_model
from src.llm.prompts import prompt_manager
from src.exceptions import AIProviderError, PromptNotFoundError

logger = logging.getLogger(__name__)

def safe_generate_and_evaluate(chat_history, user_requirements=""):
    """
    仮の構成テンプレートを生成する（最低限構造）
    """
    structure_id = str(uuid.uuid4())

    structure = {
        "id": structure_id,
        "title": "新しいアプリ構成",
        "description": "Chat履歴から自動生成された構成テンプレート",
        "content": {
            "modules": ["chat_ui", "構成保存", "構成プレビュー"],
            "output": "Webアプリ",
        },
        "user_requirements": user_requirements
    }

    return structure

def extract_json_from_response(content: str) -> Dict[str, Any]:
    """
    応答からJSONを抽出する
    
    Args:
        content: ChatGPTの応答内容
        
    Returns:
        Dict[str, Any]: 抽出されたJSONデータ
    """
    # コードブロック内のJSONを探す
    json_start = content.find("```json")
    if json_start != -1:
        json_start = content.find("\n", json_start) + 1
        json_end = content.find("```", json_start)
        if json_end != -1:
            json_content = content[json_start:json_end].strip()
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                logger.warning(f"コードブロック内のJSONパースに失敗: {json_content}")
    
    # コードブロックなしのJSONを探す
    json_start = content.find("{")
    if json_start != -1:
        json_end = content.rfind("}") + 1
        if json_end > json_start:
            json_content = content[json_start:json_end]
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                logger.warning(f"JSONパースに失敗: {json_content}")
    
    # JSONが見つからない場合は、フォールバック用の構造を生成
    logger.warning("JSONが見つからないため、フォールバック構造を生成")
    return {
        "title": "自動生成された構成",
        "description": "ChatGPTの応答からJSONを抽出できませんでした",
        "content": {
            "error": "JSON抽出失敗",
            "original_response": content[:200] + "..." if len(content) > 200 else content
        }
    }

def generate_structure_with_chatgpt(user_input: str, structure_id: Optional[str] = None) -> Dict[str, Any]:
    """
    ChatGPTを使用して構成を生成する
    
    Args:
        user_input: ユーザーの入力内容
        structure_id: 構造ID（指定されない場合は新規生成）
        
    Returns:
        Dict[str, Any]: 生成された構成データ
    """
    logger.info(f"🚀 generate_structure_with_chatgpt開始 - user_input: {user_input[:50]}...")
    
    try:
        # 構造IDの生成
        if not structure_id:
            structure_id = str(uuid.uuid4())
        
        # プロンプトマネージャーからテンプレートを取得
        prompt = prompt_manager.get_prompt("chatgpt", "structure_generation")
        if not prompt:
            logger.error("❌ ChatGPT用のstructure_generationテンプレートが見つかりません")
            raise PromptNotFoundError("chatgpt", "structure_generation")
        
        # プロンプトをフォーマット
        formatted_prompt = prompt.format(user_input=user_input)
        logger.debug(f"📝 フォーマットされたプロンプト:\n{formatted_prompt}")
        
        # ChatGPTを呼び出し（正しい引数形式で）
        content = call_model("chatgpt", "gpt-4", "structure_generation", prompt_manager, user_input=user_input)
        
        if not content:
            logger.error("❌ ChatGPTからの応答が空です")
            raise AIProviderError("ChatGPTからの応答が空です")
        
        logger.debug(f"📄 ChatGPT応答:\n{content}")
        
        # JSONを抽出
        structure_content = extract_json_from_response(content)
        
        # 必須フィールドの確認
        if "title" not in structure_content:
            structure_content["title"] = "自動生成された構成"
        if "content" not in structure_content:
            structure_content["content"] = {"description": "構成内容が生成できませんでした"}
        
        # 完全な構造データを作成
        structure = {
            "id": structure_id,
            "title": structure_content.get("title", "自動生成された構成"),
            "description": structure_content.get("description", ""),
            "content": structure_content.get("content", {}),
            "user_requirements": user_input,
            "generated_at": str(uuid.uuid1()),
            "provider": "chatgpt"
        }
        
        logger.info(f"✅ generate_structure_with_chatgpt完了 - structure_id: {structure_id}")
        return structure
        
    except Exception as e:
        logger.error(f"❌ generate_structure_with_chatgptエラー: {str(e)}")
        # フォールバック用の基本構造を返す
        return {
            "id": structure_id or str(uuid.uuid4()),
            "title": "エラーにより生成された構成",
            "description": f"構成生成中にエラーが発生しました: {str(e)}",
            "content": {
                "error": str(e),
                "user_input": user_input
            },
            "user_requirements": user_input,
            "generated_at": str(uuid.uuid1()),
            "provider": "chatgpt",
            "error": True
        }

def generate_simple_structure(title: str, description: str = "") -> Dict[str, Any]:
    """
    シンプルな構成を生成する（テスト用）
    
    Args:
        title: 構成タイトル
        description: 構成説明
        
    Returns:
        Dict[str, Any]: 生成された構成データ
    """
    structure_id = str(uuid.uuid4())
    
    return {
        "id": structure_id,
        "title": title,
        "description": description,
        "content": {
            "目的": "この構成の目的",
            "機能": {
                "主要機能": "主要な機能の説明",
                "サブ機能": "サブ機能の説明"
            },
            "技術要件": {
                "フロントエンド": "React/Vue.js等",
                "バックエンド": "Python/Node.js等",
                "データベース": "PostgreSQL/MongoDB等"
            }
        },
        "user_requirements": f"タイトル: {title}, 説明: {description}",
        "generated_at": str(uuid.uuid1()),
        "provider": "manual"
    }
