from typing import Dict, Any, Optional, List
from src.types import StructureDict, UIComponent

def render_html_from_structure(structure: StructureDict) -> str:
    """
    構造からHTMLを生成する
    
    Args:
        structure (StructureDict): 構造データ
        
    Returns:
        str: 生成されたHTML
    """
    html = []
    
    # タイトル
    if structure.get("title"):
        html.append(f"<h1>{structure['title']}</h1>")
    
    # 説明
    if structure.get("description"):
        html.append(f"<p>{structure['description']}</p>")
    
    # コンテンツ
    content = structure.get("content", {})
    if content:
        html.append("<div class='content'>")
        for key, value in content.items():
            if isinstance(value, dict):
                html.append(f"<div class='section' id='{key}'>")
                html.append(f"<h2>{key}</h2>")
                for subkey, subvalue in value.items():
                    html.append(f"<div class='item' id='{subkey}'>")
                    html.append(f"<h3>{subkey}</h3>")
                    html.append(f"<p>{subvalue}</p>")
                    html.append("</div>")
                html.append("</div>")
        html.append("</div>")
    
    return "\n".join(html) 