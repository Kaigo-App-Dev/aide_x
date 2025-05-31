import json

def validate_structure(structure):
    """
    構成テンプレート（dict）を検証し、エラーを返す。
    正常な場合は空のリスト [] を返す。
    """
    errors = []

    # 必須項目チェック
    for field in ['id', 'title', 'content']:
        if field not in structure or not structure[field]:
            errors.append(f"'{field}' が空です。")

    # content を JSON としてパース可能かチェック
    try:
        json.loads(structure['content'])
    except Exception as e:
        errors.append(f"'content' のJSON構文エラー: {str(e)}")

    return errors
