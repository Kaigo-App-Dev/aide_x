"""
差分比較モジュール
"""
import difflib
from typing import List, Dict, Any, Optional
from src.types import DiffResult, StructureDict

def get_diff_highlighted(original: str, transformed: str) -> str:
    """
    original と transformed の文字列を比較して、
    変更点を <mark> / <del> でハイライトした HTML を返す

    Args:
        original: 元の文字列
        transformed: 変換後の文字列

    Returns:
        str: ハイライトされたHTML文字列
    """
    diff = difflib.ndiff(original.splitlines(), transformed.splitlines())
    result_lines: List[str] = []
    for line in diff:
        if line.startswith("+ "):
            result_lines.append(f"<mark style='background-color:#d0ffd0;'>{line[2:]}</mark>")
        elif line.startswith("- "):
            result_lines.append(f"<del style='color:red;'>{line[2:]}</del>")
        elif line.startswith("  "):
            result_lines.append(line[2:])
    return "\n".join(result_lines)

def diff_structures(old: StructureDict, new: StructureDict) -> DiffResult:
    """
    2つの構成の差分を計算する
    
    Args:
        old (StructureDict): 古い構成
        new (StructureDict): 新しい構成
        
    Returns:
        DiffResult: 差分の結果
    """
    result: DiffResult = {
        "added": [],
        "removed": [],
        "changed": [],
        "context": {
            "old_title": old.get("title", ""),
            "new_title": new.get("title", ""),
            "old_description": old.get("description", ""),
            "new_description": new.get("description", "")
        }
    }
    
    # タイトルの変更を確認
    if old.get("title") != new.get("title"):
        result["changed"].append({
            "field": "title",
            "old": old.get("title", ""),
            "new": new.get("title", "")
        })
    
    # 説明の変更を確認
    if old.get("description") != new.get("description"):
        result["changed"].append({
            "field": "description",
            "old": old.get("description", ""),
            "new": new.get("description", "")
        })
    
    # コンテンツの変更を確認
    old_content = old.get("content", {})
    new_content = new.get("content", {})
    
    # 追加された項目
    for key in new_content:
        if key not in old_content:
            result["added"].append({
                "field": key,
                "value": new_content[key]
            })
    
    # 削除された項目
    for key in old_content:
        if key not in new_content:
            result["removed"].append({
                "field": key,
                "value": old_content[key]
            })
    
    # 変更された項目
    for key in old_content:
        if key in new_content and old_content[key] != new_content[key]:
            result["changed"].append({
                "field": key,
                "old": old_content[key],
                "new": new_content[key]
            })
    
    return result 