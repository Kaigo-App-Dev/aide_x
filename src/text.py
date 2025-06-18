from markupsafe import Markup
from typing import Dict, Any, List, Optional
from src.types import StructureDict, UIComponent

def nl2br(value: Optional[str]) -> str:
    """
    改行を<br>タグに変換する
    
    Args:
        value (Optional[str]): 変換する文字列
        
    Returns:
        str: 変換後の文字列
    """
    if not value:
        return ""
    return str(Markup(value.replace("\n", "<br>")))

def text_to_components(text: str) -> List[UIComponent]:
    """
    テキストをUIコンポーネントに変換する
    
    Args:
        text (str): 変換するテキスト
        
    Returns:
        List[UIComponent]: 変換後のUIコンポーネントのリスト
    """
    components = []
    lines = text.split("\n")
    
    for line in lines:
        if line.strip():
            components.append({
                "type": "text",
                "content": line,
                "style": {"margin": "0.5em 0"}
            })
    
    return components

def structure_to_text(structure: StructureDict) -> str:
    """
    構造をテキストに変換する
    
    Args:
        structure (StructureDict): 変換する構造
        
    Returns:
        str: 変換後のテキスト
    """
    lines = []
    
    # タイトル
    if structure.get("title"):
        lines.append(f"# {structure['title']}")
        lines.append("")
    
    # 説明
    if structure.get("description"):
        lines.append(structure["description"])
        lines.append("")
    
    # コンテンツ
    content = structure.get("content", {})
    if content:
        for key, value in content.items():
            if isinstance(value, dict):
                lines.append(f"## {key}")
                for subkey, subvalue in value.items():
                    lines.append(f"### {subkey}")
                    lines.append(str(subvalue))
                    lines.append("")
    
    return "\n".join(lines) 