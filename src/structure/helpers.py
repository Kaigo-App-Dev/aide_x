"""
Structure helpers for AIDE-X
"""
import json
import logging
import re
from typing import Dict, Any, List, Optional
from src.llm.controller import controller

logger = logging.getLogger(__name__)

def get_minimum_structure_with_gpt(content: str) -> Dict[str, Any]:
    """
    ChatGPTの抽象的な応答から最低限の構造（title, description, modules）を抽出する
    
    Args:
        content (str): ChatGPTの応答内容
        
    Returns:
        Dict[str, Any]: 最低限の構造辞書
        {
            "title": "○○○",
            "description": "○○○のためのアプリです。",
            "modules": [
                {"name": "○○", "detail": "○○○○"},
                ...
            ]
        }
    """
    try:
        logger.info("🔍 ChatGPT応答から最低限構造を抽出開始")
        logger.debug(f"入力内容: {content[:200]}...")
        
        # 1. 既存のJSON抽出を試行
        extracted_json = extract_json_part(content)
        if extracted_json and not extracted_json.get("error"):
            logger.info("✅ 既存のJSON抽出に成功")
            return normalize_minimum_structure(extracted_json)
        
        # 2. 自然言語から構造を推測
        logger.info("🔍 自然言語から構造を推測開始")
        
        # ChatGPTに構造抽出を依頼
        prompt = f"""
以下のChatGPTの応答から、最低限の構成情報を抽出してください。

応答内容:
{content}

以下の形式でJSONを返してください:
{{
  "title": "アプリのタイトル",
  "description": "アプリの説明",
  "modules": [
    {{
      "name": "モジュール名",
      "detail": "モジュールの詳細説明"
    }}
  ]
}}

注意:
- title: アプリの目的や機能を表す簡潔なタイトル
- description: アプリの概要説明
- modules: 主要な機能モジュールのリスト（3-8個程度）
- 応答内容から推測できる範囲で構いません
- 必ず有効なJSON形式で返してください
"""

        try:
            response = controller.call(
                provider="chatgpt",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            response_content = (
                response.get('content', '') if isinstance(response, dict)
                else str(response) if response is not None
                else ''
            )
            
            logger.debug(f"構造抽出応答: {response_content}")
            
            # 応答からJSONを抽出
            extracted_structure = extract_json_part(response_content)
            if extracted_structure and not extracted_structure.get("error"):
                logger.info("✅ 構造抽出に成功")
                return normalize_minimum_structure(extracted_structure)
            
        except Exception as e:
            logger.warning(f"構造抽出API呼び出し失敗: {e}")
        
        # 3. フォールバック: 基本的な構造を生成
        logger.info("⚠️ フォールバック構造を生成")
        return create_fallback_structure(content)
        
    except Exception as e:
        logger.error(f"最小構造抽出でエラー: {e}")
        return create_fallback_structure(content)

def extract_json_part(text: str) -> Dict[str, Any]:
    """
    テキストからJSON部分を抽出（簡易版）
    
    Args:
        text (str): JSONを含む可能性のあるテキスト
        
    Returns:
        Dict[str, Any]: 抽出されたJSONデータ（失敗時はエラーメッセージを含む辞書）
    """
    if not text or not text.strip():
        return {"error": "空のテキストが提供されました"}
    
    # コードブロック（```json ... ```）を優先的に検索
    code_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    code_match = re.search(code_block_pattern, text)
    if code_match:
        json_str = code_match.group(1).strip()
        try:
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            pass
    
    # 通常のJSONオブジェクトを検索
    json_pattern = r'\{[\s\S]*?\}'
    matches = list(re.finditer(json_pattern, text))
    
    if matches:
        # 最も長いJSONオブジェクトを選択
        longest_match = max(matches, key=lambda m: len(m.group(0)))
        json_str = longest_match.group(0)
        
        # 未クオートキーの修復
        json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
        
        # 末尾のカンマを削除
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        try:
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            pass
    
    return {"error": "有効なJSONオブジェクトが見つかりませんでした"}

def normalize_minimum_structure(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    抽出された構造を最低限の形式に正規化
    
    Args:
        structure (Dict[str, Any]): 抽出された構造
        
    Returns:
        Dict[str, Any]: 正規化された最低限構造
    """
    normalized = {
        "title": "",
        "description": "",
        "modules": []
    }
    
    # titleの抽出
    if "title" in structure:
        normalized["title"] = str(structure["title"]).strip()
    elif "name" in structure:
        normalized["title"] = str(structure["name"]).strip()
    
    # descriptionの抽出
    if "description" in structure:
        normalized["description"] = str(structure["description"]).strip()
    elif "summary" in structure:
        normalized["description"] = str(structure["summary"]).strip()
    
    # modulesの抽出
    if "modules" in structure and isinstance(structure["modules"], list):
        normalized["modules"] = structure["modules"]
    elif "content" in structure and isinstance(structure["content"], dict):
        # contentからmodulesを抽出
        content = structure["content"]
        if "modules" in content and isinstance(content["modules"], list):
            normalized["modules"] = content["modules"]
        elif "sections" in content and isinstance(content["sections"], list):
            # sectionsをmodulesに変換
            normalized["modules"] = [
                {"name": section.get("name", f"セクション{i+1}"), 
                 "detail": section.get("description", section.get("detail", ""))}
                for i, section in enumerate(content["sections"])
            ]
    
    # デフォルト値の設定
    if not normalized["title"]:
        normalized["title"] = "自動生成されたアプリ構成"
    if not normalized["description"]:
        normalized["description"] = "ChatGPTの応答から自動生成されたアプリ構成です。"
    if not normalized["modules"]:
        normalized["modules"] = [
            {"name": "メイン機能", "detail": "アプリの主要機能"},
            {"name": "データ管理", "detail": "データの保存・取得機能"},
            {"name": "ユーザーインターフェース", "detail": "ユーザーとの対話機能"}
        ]
    
    return normalized

def create_fallback_structure(content: str) -> Dict[str, Any]:
    """
    フォールバック用の基本構造を生成
    
    Args:
        content (str): 元の応答内容
        
    Returns:
        Dict[str, Any]: フォールバック構造
    """
    # 内容からキーワードを抽出してタイトルを生成
    title = "自動生成されたアプリ構成"
    description = "ChatGPTの応答から自動生成されたアプリ構成です。"
    
    # 内容からキーワードを抽出
    keywords = extract_keywords_from_content(content)
    if keywords:
        title = f"{keywords[0]}アプリ"
        description = f"{', '.join(keywords[:3])}を含むアプリケーションです。"
    
    return {
        "title": title,
        "description": description,
        "modules": [
            {"name": "メイン機能", "detail": "アプリの主要機能"},
            {"name": "データ管理", "detail": "データの保存・取得機能"},
            {"name": "ユーザーインターフェース", "detail": "ユーザーとの対話機能"},
            {"name": "設定管理", "detail": "アプリの設定機能"},
            {"name": "エラー処理", "detail": "エラーハンドリング機能"}
        ]
    }

def extract_keywords_from_content(content: str) -> List[str]:
    """
    内容からキーワードを抽出
    
    Args:
        content (str): 抽出対象の内容
        
    Returns:
        List[str]: 抽出されたキーワードのリスト
    """
    # 日本語のキーワードを抽出
    japanese_keywords = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}', content)
    
    # 英語のキーワードを抽出
    english_keywords = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
    
    # 重複を除去して上位10個を返す
    all_keywords = list(set(japanese_keywords + english_keywords))
    return all_keywords[:10] 