"""
Structure preview module for AIDE-X
"""
import json
from typing import Dict, Any, List, Union

def render_html_from_structure(structure: Dict[str, Any]) -> str:
    """
    Generate HTML form or simple preview from structure template (JSON)
    Supports fields / sections / pages with flexible and readable layout
    
    Args:
        structure (Dict[str, Any]): Structure template
        
    Returns:
        str: Generated HTML
    """
    def safe_html(text: str) -> str:
        """Escape HTML special characters"""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html_parts = ['<div style="font-family: sans-serif;">']

    # Pages format (priority display)
    if isinstance(structure, dict) and "pages" in structure:
        html_parts.append('<h3>🗂 ページ構成プレビュー</h3>')
        for page in structure.get("pages", []):
            page_title = page.get("title", "無題ページ")
            html_parts.append(f'<h4 style="border-bottom:1px solid #ccc;">📄 {safe_html(page_title)}</h4>')
            for section in page.get("sections", []):
                html_parts.append(f'<div style="margin-left: 1em;">')
                section_title = section.get("title", "セクション")
                html_parts.append(f'<h5>{safe_html(section_title)}</h5><form>')
                for field in section.get("fields", []):
                    try:
                        label = field.get("label", "項目")
                        name = field.get("name", "unnamed")
                        field_type = field.get("type", "text")
                        html_parts.append(f'<div class="form-group" style="margin-bottom: 1em;">')
                        html_parts.append(f'<label for="{name}">{safe_html(label)}</label><br>')

                        if field_type == "text":
                            html_parts.append(f'<input type="text" id="{name}" name="{name}" style="width: 100%;"><br>')
                        elif field_type == "textarea":
                            html_parts.append(f'<textarea id="{name}" name="{name}" rows="4" style="width: 100%;"></textarea><br>')
                        elif field_type == "date":
                            html_parts.append(f'<input type="date" id="{name}" name="{name}"><br>')
                        elif field_type == "select":
                            options = field.get("options", [])
                            html_parts.append(f'<select id="{name}" name="{name}">')
                            for opt in options:
                                html_parts.append(f'<option value="{safe_html(opt)}">{safe_html(opt)}</option>')
                            html_parts.append('</select><br>')
                        else:
                            html_parts.append(f'<input type="{field_type}" id="{name}" name="{name}"><br>')
                        html_parts.append('</div>')
                    except Exception as e:
                        html_parts.append(f'<p style="color:red;">⚠ 項目の表示に失敗しました: {e}</p>')
                html_parts.append('</form><hr></div>')

    # Form format (fields only)
    elif "fields" in structure:
        html_parts.append('<h3>📝 入力フォームプレビュー</h3><form>')
        for field in structure.get("fields", []):
            try:
                label = field.get("label", "項目")
                name = field.get("name", "unnamed")
                field_type = field.get("type", "text")
                html_parts.append(f'<div class="form-group" style="margin-bottom: 1em;">')
                html_parts.append(f'<label for="{name}">{safe_html(label)}</label><br>')

                if field_type == "text":
                    html_parts.append(f'<input type="text" id="{name}" name="{name}" style="width: 100%;"><br>')
                elif field_type == "textarea":
                    html_parts.append(f'<textarea id="{name}" name="{name}" rows="4" style="width: 100%;"></textarea><br>')
                elif field_type == "date":
                    html_parts.append(f'<input type="date" id="{name}" name="{name}"><br>')
                elif field_type == "select":
                    options = field.get("options", [])
                    html_parts.append(f'<select id="{name}" name="{name}">')
                    for opt in options:
                        html_parts.append(f'<option value="{safe_html(opt)}">{safe_html(opt)}</option>')
                    html_parts.append('</select><br>')
                else:
                    html_parts.append(f'<input type="{field_type}" id="{name}" name="{name}"><br>')
                html_parts.append('</div>')
            except Exception as e:
                html_parts.append(f'<p style="color:red;">⚠ 項目の表示に失敗しました: {e}</p>')
        html_parts.append('<input type="submit" value="送信"></form>')

    # Section format (sections based)
    elif "sections" in structure:
        sections = structure.get("sections", [])
        html_parts.append('<h3>📋 セクション構成プレビュー</h3>')
        if not sections:
            html_parts.append("<p>📭 セクション情報がありません。</p>")
        else:
            for section in sections:
                label = section.get("label", "未定義ラベル")
                field_type = section.get("type", "text")
                html_parts.append(f"<p>・<strong>{safe_html(label)}</strong>（type: <code>{safe_html(field_type)}</code>）</p>")

    # Other format (key-value)
    else:
        html_parts.append('<h3>🔎 その他の構成プレビュー</h3><hr>')
        try:
            for k, v in structure.items():
                val = json.dumps(v, ensure_ascii=False, indent=2) if isinstance(v, (dict, list)) else str(v)
                html_parts.append(f"<p><strong>{safe_html(k)}</strong><br><pre style='background:#f5f5f5;padding:0.5em;border:1px solid #ddd;'>{safe_html(val)}</pre></p>")
        except Exception as e:
            html_parts.append(f'<p style="color:red;">⚠ 表示エラー: {e}</p>')

    html_parts.append('</div>')
    return "\n".join(html_parts) 