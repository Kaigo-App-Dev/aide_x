import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

def get_structure_history_dir():
    base_dir = os.environ.get('AIDEX_DATA_DIR', '.')
    return os.path.join(base_dir, 'structure_history')


def get_structure_history(structure_id: str) -> List[Dict[str, Any]]:
    """指定IDのStructureHistory一覧を取得"""
    history_list = []
    dir_path = get_structure_history_dir()
    if not os.path.exists(dir_path):
        return history_list
    for fname in os.listdir(dir_path):
        if fname.endswith(".json") and structure_id in fname:
            with open(os.path.join(dir_path, fname), encoding="utf-8") as f:
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
    dir_path = get_structure_history_dir()
    path = os.path.join(dir_path, f"{history_id}.json")
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


def save_structure_history(structure_id: str,
                          structure: dict,
                          provider: str,
                          score: Optional[float] = None,
                          comment: str = "",
                          timestamp: Optional[str] = None) -> bool:
    """
    Claude評価結果・Gemini補完結果の履歴をJSONL形式で保存
    
    Args:
        structure_id (str): 構造ID
        structure (dict): 保存する構造データ（claude_evaluation や gemini_output を含む）
        provider (str): プロバイダー名（"claude" または "gemini"）
        score (float, optional): 評価スコア（Claude評価の場合）
        comment (str): コメント
        timestamp (str, optional): タイムスタンプ（指定しない場合は現在時刻）
        
    Returns:
        bool: 保存成功時True、失敗時False
    """
    try:
        # 保存先ディレクトリの作成
        dir_path = get_structure_history_dir()
        os.makedirs(dir_path, exist_ok=True)
        
        # ファイルパス
        file_path = os.path.join(dir_path, f"{structure_id}.jsonl")
        
        # タイムスタンプの設定
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # 要求された形式で保存データを作成
        history_entry = {
            "timestamp": timestamp,
            "role": "assistant",
            "source": provider,
            "content": structure
        }
        
        # スコアがある場合は追加
        if score is not None:
            history_entry["score"] = score
        
        # コメントがある場合は追加
        if comment:
            history_entry["comment"] = comment
        
        # JSONL形式で追記保存
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(history_entry, ensure_ascii=False) + "\n")
        
        print(f"✅ 構造履歴を保存しました: {file_path} (provider: {provider})")
        return True
        
    except Exception as e:
        print(f"❌ 構造履歴保存中にエラーが発生: {str(e)}")
        return False


def load_structure_history(structure_id: str) -> List[Dict[str, Any]]:
    """指定IDの構造履歴（JSONL）を新しい順で返す"""
    dir_path = get_structure_history_dir()
    file_path = os.path.join(dir_path, f"{structure_id}.jsonl")
    history_list = []
    if not os.path.exists(file_path):
        return history_list
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                history_list.append(entry)
            except Exception as e:
                print(f"⚠️ JSONL行の解析に失敗: {e}")
                continue
    # timestamp降順で返す
    history_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    print(f"📖 構造履歴を読み込みました: {len(history_list)}件")
    return history_list


def get_structure_history_by_provider(structure_id: str, provider: str) -> List[Dict[str, Any]]:
    """プロバイダー別の履歴を新しい順で返す"""
    all_history = load_structure_history(structure_id)
    filtered = [h for h in all_history if h.get("source") == provider]
    print(f"📖 {provider}履歴を読み込みました: {len(filtered)}件")
    return filtered


def get_latest_structure_history(structure_id: str, provider: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """最新の履歴を返す（provider指定可）"""
    if provider:
        history = get_structure_history_by_provider(structure_id, provider)
    else:
        history = load_structure_history(structure_id)
    if not history:
        return None
    return history[0]


def compare_structure_history(structure_id: str, index1: int = 0, index2: int = 1) -> Optional[Dict[str, Any]]:
    """
    2つの履歴エントリを比較
    
    Args:
        structure_id (str): 構造ID
        index1 (int): 比較対象1のインデックス
        index2 (int): 比較対象2のインデックス
        
    Returns:
        Optional[Dict[str, Any]]: 比較結果、失敗時はNone
    """
    try:
        history_list = load_structure_history(structure_id)
        
        if len(history_list) <= max(index1, index2):
            print(f"❌ 履歴インデックスが範囲外: {index1}, {index2} (最大: {len(history_list) - 1})")
            return None
        
        entry1 = history_list[index1]
        entry2 = history_list[index2]
        
        # 差分計算（簡易版）
        diff_result = {
            "structure_id": structure_id,
            "entry1": entry1,
            "entry2": entry2,
            "differences": {}
        }
        
        # 構造データの差分を計算
        structure1 = entry1.get("content", {})
        structure2 = entry2.get("content", {})
        
        # タイトルの差分
        if structure1.get("title") != structure2.get("title"):
            diff_result["differences"]["title"] = {
                "from": structure1.get("title"),
                "to": structure2.get("title")
            }
        
        # モジュール数の差分
        modules1 = structure1.get("modules", {})
        modules2 = structure2.get("modules", {})
        if len(modules1) != len(modules2):
            diff_result["differences"]["module_count"] = {
                "from": len(modules1),
                "to": len(modules2)
            }
        
        print(f"✅ 履歴比較完了: {index1} vs {index2}")
        return diff_result
        
    except Exception as e:
        print(f"❌ 履歴比較中にエラーが発生: {str(e)}")
        return None


def cleanup_old_structure_history(days_to_keep: int = 30) -> int:
    """
    古い履歴ファイルを削除
    
    Args:
        days_to_keep (int): 保持する日数
        
    Returns:
        int: 削除されたファイル数
    """
    try:
        dir_path = get_structure_history_dir()
        if not os.path.exists(dir_path):
            return 0
        
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        for filename in os.listdir(dir_path):
            if filename.endswith(".jsonl"):
                file_path = os.path.join(dir_path, filename)
                file_mtime = os.path.getmtime(file_path)
                
                if file_mtime < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"🗑️ 古い履歴ファイルを削除: {filename}")
        
        print(f"✅ 古い履歴ファイルの削除完了: {deleted_count}件")
        return deleted_count
        
    except Exception as e:
        print(f"❌ 古い履歴ファイル削除中にエラーが発生: {str(e)}")
        return 0 