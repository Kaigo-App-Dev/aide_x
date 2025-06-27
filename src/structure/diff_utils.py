import json
from typing import Any, Dict

def generate_diff_html(before_content: Dict[str, Any], after_content: Dict[str, Any]) -> str:
    """DeepDiffを使用して差分HTMLを生成"""
    try:
        from deepdiff import DeepDiff
        diff = DeepDiff(before_content, after_content, ignore_order=True)
        if not diff:
            return '<span class="no-changes">変更なし</span>'
        html_parts = []
        # 追加
        if 'dictionary_item_added' in diff:
            html_parts.append('<div class="diff-section"><h4>➕ 追加された項目:</h4>')
            for path in diff['dictionary_item_added']:
                value = get_nested_value(after_content, path)
                html_parts.append(f'<div class="diff-item"><span class="diff-path">{path}</span>: <span class="diff-added">{json.dumps(value, ensure_ascii=False)}</span></div>')
            html_parts.append('</div>')
        # 削除
        if 'dictionary_item_removed' in diff:
            html_parts.append('<div class="diff-section"><h4>➖ 削除された項目:</h4>')
            for path in diff['dictionary_item_removed']:
                value = get_nested_value(before_content, path)
                html_parts.append(f'<div class="diff-item"><span class="diff-path">{path}</span>: <span class="diff-removed">{json.dumps(value, ensure_ascii=False)}</span></div>')
            html_parts.append('</div>')
        # 変更
        if 'values_changed' in diff:
            html_parts.append('<div class="diff-section"><h4>🔄 変更された項目:</h4>')
            for path, change_info in diff['values_changed'].items():
                old_value = change_info['old_value']
                new_value = change_info['new_value']
                html_parts.append(f'''
                    <div class="diff-item">
                        <span class="diff-path">{path}</span>:<br>
                        <span class="diff-removed">旧: {json.dumps(old_value, ensure_ascii=False)}</span><br>
                        <span class="diff-added">新: {json.dumps(new_value, ensure_ascii=False)}</span>
                    </div>
                ''')
            html_parts.append('</div>')
        return ''.join(html_parts)
    except ImportError:
        return generate_simple_diff_html(before_content, after_content)
    except Exception as e:
        return f'<span class="diff-error">差分生成エラー: {str(e)}</span>'

def get_nested_value(data, path):
    try:
        keys = path.strip("root['").rstrip("']").split("']['")
        value = data
        for key in keys:
            value = value[key]
        return value
    except Exception:
        return None

def generate_simple_diff_html(before_content, after_content):
    before_str = json.dumps(before_content, ensure_ascii=False, indent=2)
    after_str = json.dumps(after_content, ensure_ascii=False, indent=2)
    if before_str == after_str:
        return '<span class="no-changes">変更なし</span>'
    return f'''
        <div class="diff-section">
            <h4>📄 構成変更:</h4>
            <div class="diff-simple">
                <div class="diff-before">
                    <strong>変更前:</strong><br>
                    <pre>{before_str}</pre>
                </div>
                <div class="diff-after">
                    <strong>変更後:</strong><br>
                    <pre>{after_str}</pre>
                </div>
            </div>
        </div>
    ''' 