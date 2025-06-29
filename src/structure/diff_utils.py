import json
from typing import Any, Dict, List

def generate_module_diff(before_modules: List[Dict[str, Any]], after_modules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    名前ベースで差分を抽出し、追加・削除・変更を分類
    
    Args:
        before_modules: Claude構成のモジュールリスト
        after_modules: Gemini補完のモジュールリスト
        
    Returns:
        Dict containing 'added', 'removed', 'changed' module lists
    """
    try:
        # モジュールを名前で辞書化
        before_dict = {}
        after_dict = {}
        
        # before_modulesの処理
        for module in before_modules:
            module_name = module.get("name") or module.get("title") or str(module)
            before_dict[module_name] = module
        
        # after_modulesの処理
        for module in after_modules:
            module_name = module.get("name") or module.get("title") or str(module)
            after_dict[module_name] = module
        
        # 差分の計算
        added = []
        removed = []
        changed = []
        
        # 追加されたモジュール
        for name in after_dict:
            if name not in before_dict:
                added.append(after_dict[name])
        
        # 削除されたモジュール
        for name in before_dict:
            if name not in after_dict:
                removed.append(before_dict[name])
        
        # 変更されたモジュール
        for name in after_dict:
            if name in before_dict:
                before_module = before_dict[name]
                after_module = after_dict[name]
                
                # モジュールの内容を比較
                if json.dumps(before_module, sort_keys=True) != json.dumps(after_module, sort_keys=True):
                    changed.append({
                        "name": name,
                        "before": before_module,
                        "after": after_module,
                        "changes": get_module_changes(before_module, after_module)
                    })
        
        return {
            "added": added,
            "removed": removed,
            "changed": changed
        }
        
    except Exception as e:
        print(f"❌ モジュール差分生成エラー: {str(e)}")
        return {
            "added": [],
            "removed": [],
            "changed": []
        }

def get_module_changes(before_module: Dict[str, Any], after_module: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    モジュール内の変更を詳細に分析
    
    Args:
        before_module: 変更前のモジュール
        after_module: 変更後のモジュール
        
    Returns:
        List of change details
    """
    changes = []
    
    # 全フィールドを収集
    all_fields = set(before_module.keys()) | set(after_module.keys())
    
    for field in all_fields:
        before_value = before_module.get(field)
        after_value = after_module.get(field)
        
        if before_value != after_value:
            changes.append({
                "field": field,
                "before": before_value,
                "after": after_value,
                "type": "modified"
            })
    
    return changes

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