from markupsafe import Markup
from typing import Dict, Any, List, Optional
from src.common.types import StructureDict, UIComponent

def nl2br(value: Optional[str]) -> str:
    """
    改行を<br>タグに変換するJinja2フィルター
    
    Args:
        value (Optional[str]): 変換する文字列
        
    Returns:
        str: 変換後の文字列
    """
    if not value:
        return ''
    return Markup(value.replace('\n', '<br>'))

def format_structure_text(structure: StructureDict) -> str:
    """
    構成をテキスト形式にフォーマットする
    
    Args:
        structure (StructureDict): フォーマット対象の構成
        
    Returns:
        str: フォーマットされたテキスト
    """
    text_parts = []
    
    # タイトル
    if structure.get("title"):
        text_parts.append(f"# {structure['title']}")
        text_parts.append("")
    
    # 説明
    if structure.get("description"):
        text_parts.append(structure["description"])
        text_parts.append("")
    
    # コンテンツ
    content = structure.get("content", {})
    if content:
        for key, value in content.items():
            text_parts.append(f"## {key}")
            if isinstance(value, dict):
                for k, v in value.items():
                    text_parts.append(f"- {k}: {v}")
            else:
                text_parts.append(str(value))
            text_parts.append("")
    
    return "\n".join(text_parts)

def format_ui_components(components: List[UIComponent]) -> str:
    """
    UIコンポーネントをテキスト形式にフォーマットする
    
    Args:
        components (List[UIComponent]): フォーマット対象のUIコンポーネント
        
    Returns:
        str: フォーマットされたテキスト
    """
    text_parts = []
    
    for component in components:
        if component["type"] == "title":
            level = component.get("level", 1)
            text_parts.append(f"{'#' * level} {component['content']}")
        elif component["type"] == "description":
            text_parts.append(component["content"])
        elif component["type"] == "section":
            text_parts.append(f"## {component['title']}")
            if isinstance(component["content"], dict):
                for k, v in component["content"].items():
                    text_parts.append(f"- {k}: {v}")
            else:
                text_parts.append(str(component["content"]))
        text_parts.append("")
    
    return "\n".join(text_parts) 