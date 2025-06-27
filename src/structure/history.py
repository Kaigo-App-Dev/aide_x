import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

HISTORY_DIR = os.path.join("data", "history")


def get_structure_history(structure_id: str) -> List[Dict[str, Any]]:
    """指定IDのStructureHistory一覧を取得"""
    history_list = []
    if not os.path.exists(HISTORY_DIR):
        return history_list
    for fname in os.listdir(HISTORY_DIR):
        if fname.endswith(".json") and structure_id in fname:
            with open(os.path.join(HISTORY_DIR, fname), encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    history_list.append(data)
                except Exception:
                    continue
    # timestamp降順
    history_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return history_list


def get_history_by_id(history_id: str) -> Optional[Dict[str, Any]]:
    """history_idで履歴を取得"""
    path = os.path.join(HISTORY_DIR, f"{history_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def restore_structure_from_history(structure_id: str, history_id: str) -> bool:
    """指定履歴から構成を復元"""
    history = get_history_by_id(history_id)
    if not history:
        return False
    # 構成ファイルパス
    structure_path = os.path.join("data", f"{structure_id}.json")
    # 上書き保存
    with open(structure_path, "w", encoding="utf-8") as f:
        json.dump(history["content"], f, ensure_ascii=False, indent=2)
    return True 