import json

def evaluate_structure_content(content_json_str):
    try:
        content = json.loads(content_json_str)
    except json.JSONDecodeError:
        return {
            "intent_match": 0,
            "quality_score": 0,
            "intent_reason": "JSON構文エラー。評価できませんでした。"
        }

    # 仮の評価ロジック
    intent_match = 85
    quality_score = 75
    intent_reason = "構成は一般的なテンプレート構造に沿っており、モジュール分離も適切です。"

    return {
        "intent_match": intent_match,
        "quality_score": quality_score,
        "intent_reason": intent_reason
    }
