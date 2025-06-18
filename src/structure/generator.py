# utils/generator.py

import uuid

def safe_generate_and_evaluate(chat_history, user_requirements=""):
    """
    仮の構成テンプレートを生成する（最低限構造）
    """
    structure_id = str(uuid.uuid4())

    structure = {
        "id": structure_id,
        "title": "新しいアプリ構成",
        "description": "Chat履歴から自動生成された構成テンプレート",
        "content": {
            "modules": ["chat_ui", "構成保存", "構成プレビュー"],
            "output": "Webアプリ",
        },
        "user_requirements": user_requirements
    }

    return structure
