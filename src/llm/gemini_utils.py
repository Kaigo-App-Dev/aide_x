def call_gemini_ui(structure: dict) -> dict:
    # Claude/Gemini連携時のUI構成補完処理をここにまとめて記述
    if not isinstance(structure.get("content"), dict):
        structure["content"] = {}
    structure["content"]["ui_params"] = {"theme": "light", "layout": "responsive"}
    return structure 