import os
import json
from datetime import datetime
from uuid import uuid4

# 構造テンプレート保存ディレクトリ
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def get_structure_path(structure_id):
    return os.path.join(DATA_DIR, f"{structure_id}.json")

def save_structure(structure, is_final=False):
    os.makedirs(DATA_DIR, exist_ok=True)

    # ✅ str型ならdictに変換、空文字チェックも追加
    if isinstance(structure, str):
        if not structure.strip():
            raise ValueError("⚠ 保存失敗：空のJSON文字列です。")
        try:
            structure = json.loads(structure)
        except json.JSONDecodeError:
            raise ValueError("⚠ 保存失敗：構造テンプレートが不正なJSONです。")

    if not isinstance(structure, dict):
        raise ValueError("⚠ 保存失敗：structure が dict ではありません。")

    structure['is_final'] = is_final
    filename = get_structure_path(structure['id'])

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

def load_structures():
    os.makedirs(DATA_DIR, exist_ok=True)
    structures = []
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith('.json'):
            continue
        path = os.path.join(DATA_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # ファイルの最終更新日時を付与
                updated_at = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
                data['updated_at'] = updated_at
                structures.append(data)
        except Exception as e:
            print(f"読み込み失敗: {filename} → {e}")
    return structures

def load_structure_by_id(structure_id):
    path = get_structure_path(structure_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"id": structure_id, "title": "", "description": "", "content": ""}

def append_structure_log(structure, action, detail=""):
    now = datetime.now().isoformat()

    log_entry = {
        "timestamp": now,
        "action": action,
        "detail": detail,
        "snapshot": {
            "content": structure.get("content", ""),
            "title": structure.get("title", ""),
            "description": structure.get("description", "")
        }
    }

    if "history" not in structure:
        structure["history"] = []

    structure["history"].append(log_entry)

def get_candidates_for_evolution(threshold=0.85):
    """未確定かつ評価スコアが低いテンプレートを抽出"""
    candidates = []
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data.get("is_final", False):
                    if data.get("intent_match", 1.0) < threshold:
                        candidates.append(data)
        except Exception as e:
            print(f"読み込み失敗: {filename} → {e}")
    return candidates
