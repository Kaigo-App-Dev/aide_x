import json

def normalize_structure_format(structure: dict) -> dict:
    content = structure.get("content", {})
    if isinstance(content, str):
        try:
            structure["content"] = json.loads(content)
        except Exception:
            structure["content"] = {}
    return structure 