"""
構成補完誘導メッセージ生成
"""

def generate_intervention_message(state: dict) -> str:
    """
    構成診断結果からユーザーへの補完誘導メッセージを生成
    Args:
        state: analyze_structure_state() の戻り値
    Returns:
        str: ユーザーに表示する誘導メッセージ
    """
    # 空構成
    if state.get("is_empty"):
        return "まだ構成が定義されていません。作成を始めますか？\n\n[はい] [いいえ]"

    # 完全構成
    if state.get("module_count", 0) > 0 and not state.get("incomplete_modules") and not state.get("missing_fields"):
        return ""  # メッセージ不要

    # 不完全構成
    module_count = state.get("module_count", 0)
    missing_fields = state.get("missing_fields", [])
    incomplete_modules = state.get("incomplete_modules", [])

    # 不足フィールドのリストアップ
    missing_fields_str = "、".join(missing_fields) if missing_fields else "必須項目"
    
    # 不完全なモジュール名リスト
    incomplete_names = [m.get("name", f"モジュール{m.get('index', '?')}") for m in incomplete_modules]
    incomplete_names_str = "、".join(incomplete_names)

    # メッセージ生成
    if module_count == 1:
        msg = f"構成には1個のモジュールが含まれていますが、いくつかの必須項目が不足しています（{missing_fields_str}）。このまま自動で補完してもよろしいですか？"
    else:
        msg = f"構成には{module_count}個のモジュールが含まれていますが、いくつかの必須項目が不足しています（{missing_fields_str}）。このまま自動で補完してもよろしいですか？"
    
    msg += "\n\n[はい] [いいえ]"
    
    # いいえ時の案内
    if incomplete_names:
        msg += f"\n\n未記入のモジュール: {incomplete_names_str}"
        msg += "\n不足項目を修正してください。"
    return msg 