from typing import Dict, Any, Optional, List
from src.types import StructureDict, UIComponent

def render_html_from_structure(structure: StructureDict) -> str:
    """
    構成からHTMLを生成する
    
    Args:
        structure (StructureDict): 構成データ
        
    Returns:
        str: 生成されたHTML
    """
    html = []
    
    # タイトル
    if structure.get("title"):
        html.append(f"<h1>{structure['title']}</h1>")
    
    # 説明
    if structure.get("description"):
        html.append(f"<p class='description'>{structure['description']}</p>")
    
    # コンテンツ
    content = structure.get("content", {})
    if content:
        html.append("<div class='content'>")
        for key, value in content.items():
            html.append(f"<div class='section'>")
            html.append(f"<h2>{key}</h2>")
            if isinstance(value, dict):
                html.append("<ul>")
                for k, v in value.items():
                    html.append(f"<li><strong>{k}:</strong> {v}</li>")
                html.append("</ul>")
            else:
                html.append(f"<p>{value}</p>")
            html.append("</div>")
        html.append("</div>")
    
    return "\n".join(html)

def nl2br(text: str) -> str:
    """
    改行を<br>タグに変換する
    
    Args:
        text (str): 変換するテキスト
        
    Returns:
        str: 変換後のテキスト
    """
    return text.replace("\n", "<br>")

def get_ui_components(structure: StructureDict) -> List[UIComponent]:
    """
    構成からUIコンポーネントのリストを生成する
    
    Args:
        structure (StructureDict): 構成データ
        
    Returns:
        List[UIComponent]: UIコンポーネントのリスト
    """
    components = []
    
    # タイトルコンポーネント
    if structure.get("title"):
        components.append({
            "type": "title",
            "content": structure["title"],
            "level": 1
        })
    
    # 説明コンポーネント
    if structure.get("description"):
        components.append({
            "type": "description",
            "content": structure["description"]
        })
    
    # コンテンツコンポーネント
    content = structure.get("content", {})
    if content:
        for key, value in content.items():
            components.append({
                "type": "section",
                "title": key,
                "content": value
            })
    
    return components 