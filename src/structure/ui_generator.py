# utils/gemini_ui.py

import json
from src.llm.controller import AIController
from src.llm.providers.base import ChatMessage
from typing import Dict, Any, Optional, List, cast, TypedDict, Union
import logging
from src.common.types import StructureDict, EvaluationResult, LLMResponse

logger = logging.getLogger(__name__)

class UIComponent(TypedDict):
    type: str
    props: Dict[str, Any]
    children: Optional[Union[List['UIComponent'], str]]

def normalize_nested_dict_structure(raw_structure: dict) -> dict:
    """自由形式のdict構造を、Gemini模擬変換用のUI構成dictに変換する"""
    try:
        normalized = {}
        for group_title, contents in raw_structure.items():
            if isinstance(contents, dict):
                normalized[group_title] = {}
                for sub_key, value in contents.items():
                    if isinstance(value, str):
                        normalized[group_title][sub_key] = value
                    elif isinstance(value, list):
                        normalized[group_title][sub_key] = "\n".join(str(v) for v in value)
                    else:
                        normalized[group_title][sub_key] = str(value)
            else:
                if isinstance(contents, list):
                    normalized[group_title] = "\n".join(str(v) for v in contents)
                else:
                    normalized[group_title] = str(contents)
        return normalized
    except Exception as e:
        logger.error(f"構造の正規化中にエラーが発生: {str(e)}")
        return raw_structure


def convert_structure_to_ui_pages(free_structure: dict) -> dict:
    """Claudeの出力をUI構成に変換（正規化を含む）"""
    try:
        free_structure = normalize_nested_dict_structure(free_structure)
        pages = []
        
        for idx, (group_title, contents) in enumerate(free_structure.items(), start=1):
            page = {
                "title": group_title,
                "sections": []
            }

            if isinstance(contents, dict):
                for sec_title, value in contents.items():
                    section = {
                        "title": sec_title,
                        "fields": [
                            {
                                "label": sec_title,
                                "name": f"field_{idx}_{sec_title}",
                                "type": "text",
                                "value": value
                            }
                        ]
                    }
                    page["sections"].append(section)
            else:
                page["sections"].append({
                    "title": group_title,
                    "fields": [
                        {
                            "label": group_title,
                            "name": f"field_{idx}",
                            "type": "text",
                            "value": contents
                        }
                    ]
                })

            pages.append(page)

        return {"pages": pages}
    except Exception as e:
        logger.error(f"UIページ変換中にエラーが発生: {str(e)}")
        return {"pages": []}


def call_gemini_for_ui(structure: dict) -> dict:
    """
    Geminiを呼び出してUI構成（pages形式）を生成する。
    """
    try:
        # 入力の検証
        if not isinstance(structure, dict):
            raise ValueError("構造体は辞書型である必要があります")

        # 構造の取得と検証
        raw_json_str = structure.get("content")
        if not raw_json_str:
            raise ValueError("構造体にcontentが含まれていません")

        # JSON文字列の解析
        if isinstance(raw_json_str, str):
            try:
                free_structure = json.loads(raw_json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSONの解析に失敗しました: {str(e)}")
        else:
            free_structure = raw_json_str

        # 構造の正規化
        normalized_structure = normalize_nested_dict_structure(free_structure)
        if not normalized_structure:
            raise ValueError("構造の正規化に失敗しました")

        # UIページへの変換
        ui_structure = convert_structure_to_ui_pages(normalized_structure)
        if not ui_structure or not ui_structure.get("pages"):
            raise ValueError("UIページの生成に失敗しました")

        return ui_structure

    except Exception as e:
        logger.error(f"Gemini UI生成中にエラーが発生: {str(e)}")
        return {"pages": []}


# ✅ 簡易UI提案（suggestion型）を返す関数を追加（表示確認用）
def call_gemini_ui_generator(structure: dict) -> dict:
    """
    Geminiの提案を生成
    """
    try:
        # 構造の取得
        content = structure.get("content", {})
        if isinstance(content, str):
            content = json.loads(content)
        
        # Gemini APIを呼び出し
        messages = [
            ChatMessage(
                role="user",
                content=f"以下の構成に対して、UI設計の提案をしてください：\n{json.dumps(content, ensure_ascii=False, indent=2)}"
            )
        ]
        
        response = AIController.call(
            provider="gemini",
            messages=messages,
            model="gemini-pro",
            max_tokens=1000
        )
        
        # 応答を整形
        suggestions = []
        for line in response["content"].split("\n"):
            if line.strip() and not line.startswith(("#", "```")):
                suggestions.append(line.strip())
        
        return {
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Gemini UI提案生成中にエラーが発生: {str(e)}")
        return {"suggestions": []}


def generate_ui_with_gemini(structure: StructureDict) -> UIComponent:
    """Generate UI structure using Gemini"""
    messages = [
        ChatMessage(
            role="user",
            content=f"Generate a UI structure for:\n{json.dumps(structure, indent=2)}"
        )
    ]
    
    response = AIController.call(
        provider="gemini",
        messages=messages,
        model="gemini-pro"
    )
    
    if not response or "content" not in response:
        logger.error("Error generating UI: Invalid response format")
        return cast(UIComponent, {
            "type": "div",
            "props": {"error": "Invalid response format"},
            "children": None
        })
    
    try:
        # Parse response and ensure it matches UIComponent type
        result = json.loads(response["content"])
        return cast(UIComponent, {
            "type": str(result.get("type", "div")),
            "props": dict(result.get("props", {})),
            "children": result.get("children")
        })
    except Exception as e:
        logger.error(f"Error parsing UI response: {e}")
        return cast(UIComponent, {
            "type": "div",
            "props": {"error": str(e)},
            "children": None
        })


def normalize_structure(structure: StructureDict) -> Dict[str, Any]:
    """Normalize structure for UI generation"""
    normalized: Dict[str, Any] = {
        "title": structure.get("title", ""),
        "description": structure.get("description", ""),
        "content": structure.get("content", ""),
        "metadata": structure.get("metadata", {})
    }
    return normalized
