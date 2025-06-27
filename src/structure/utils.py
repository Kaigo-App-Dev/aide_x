"""
Structure utilities for AIDE-X
"""
import os
import json
import re
import uuid
import logging
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional, cast, TypedDict, Union, Tuple
# from src.types import StructureDict, StructureHistory  # 型エラーのため一時的にコメントアウト

# Initialize logger
logger = logging.getLogger(__name__)

# 構造テンプレート保存ディレクトリ
def get_data_dir():
    """Get the data directory from environment variable or default"""
    return os.environ.get("AIDEX_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data'))

# デバッグ出力
logger.debug(f"🔧 DATA_DIR設定: {get_data_dir()} (AIDEX_DATA_DIR: {os.environ.get('AIDEX_DATA_DIR', '未設定')})")

# 型定義を一時的にここで定義
StructureDict = Dict[str, Any]
StructureHistory = Dict[str, Any]

class StructureHistory(TypedDict):
    """構造の履歴データ型"""
    timestamp: str
    action: str
    detail: str
    snapshot: Dict[str, Any]

class StructureDict(TypedDict):
    """構造データ型"""
    id: str
    title: str
    description: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
    history: Optional[List[StructureHistory]]

def get_structure_path(structure_id: str) -> str:
    """Get the path for a structure file"""
    return os.path.join(get_data_dir(), f"{structure_id}.json")

def get_history_path(structure_id: str) -> str:
    """Get the path for a structure history file"""
    return os.path.join(get_data_dir(), f"{structure_id}_history.json")

def get_structure(structure_id: str) -> Optional[StructureDict]:
    """
    指定されたIDの構成を取得する
    
    Args:
        structure_id (str): 構成のID
        
    Returns:
        Optional[StructureDict]: 構成データ、存在しない場合はNone
    """
    try:
        file_path = f"structures/{structure_id}.json"
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading structure: {e}")
        return None

def save_structure(structure_id: str, structure: StructureDict) -> bool:
    """
    構成を保存する
    
    Args:
        structure_id (str): 構成のID
        structure (StructureDict): 保存する構成データ
        
    Returns:
        bool: 保存が成功したかどうか
    """
    try:
        # AIDEX_DATA_DIRを優先して使用
        data_dir = get_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, f"{structure_id}.json")
        
        # Convert datetime objects to strings
        structure_json = json.dumps(structure, ensure_ascii=False, indent=2, default=str)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(structure_json)
        return True
    except Exception as e:
        print(f"Error saving structure: {e}")
        return False

def get_structure_history(structure_id: str) -> Optional[StructureHistory]:
    """
    構成の履歴を取得する
    
    Args:
        structure_id (str): 構成のID
        
    Returns:
        Optional[StructureHistory]: 履歴データ、存在しない場合はNone
    """
    try:
        file_path = f"histories/{structure_id}.json"
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
        return None

def save_structure_history(history: StructureHistory, structure_id: str) -> bool:
    """
    構成の履歴を保存する
    
    Args:
        history (StructureHistory): 保存する履歴データ
        structure_id (str): 構成のID
        
    Returns:
        bool: 保存が成功したかどうか
    """
    try:
        os.makedirs("histories", exist_ok=True)
        file_path = f"histories/{structure_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving history: {e}")
        return False

def load_structures() -> List[Dict[str, Any]]:
    """Load all structures from the data directory"""
    os.makedirs(get_data_dir(), exist_ok=True)
    structures = []
    for root, dirs, files in os.walk(get_data_dir()):
        for filename in files:
            if not filename.endswith('.json') or '_history' in filename:
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Convert content string to dict if needed
                    if isinstance(data.get("content"), str):
                        try:
                            data["content"] = json.loads(data["content"])
                        except Exception as e:
                            logger.error(f"⚠ contentデコード失敗: {filename} → {e}")
                            data["content"] = {"sections": [], "pages": []}

                    # Add last modified time
                    updated_at = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
                    data['updated_at'] = updated_at

                    # Add evaluation info if present
                    evaluation = data.get("evaluation", {})
                    data["intent_match"] = round(evaluation.get("intent_match", 0) * 100, 1) if evaluation else None
                    data["quality_score"] = round(evaluation.get("quality_score", 0) * 100, 1) if evaluation else None
                    data["intent_reason"] = evaluation.get("intent_reason", "")

                    structures.append(data)
            except Exception as e:
                logger.error(f"読み込み失敗: {filename} → {e}")
    return structures

def load_structure_by_id(structure_id: str) -> Optional[Dict[str, Any]]:
    """
    指定されたIDの構成を複数の候補パスから検索して読み込む
    
    Args:
        structure_id (str): 構成のID
        
    Returns:
        Optional[Dict[str, Any]]: 構成データ、存在しない場合はNone
    """
    # 候補パスのリスト（AIDEX_DATA_DIRを最優先）
    possible_paths = [
        os.path.join(get_data_dir(), "default", f"{structure_id}.json"),  # AIDEX_DATA_DIR/default/
        os.path.join(get_data_dir(), f"{structure_id}.json"),             # AIDEX_DATA_DIR/
        f"data/default/{structure_id}.json",                        # 従来のパス（後方互換性）
        f"structures/{structure_id}.json",                          # 従来のパス（後方互換性）
        f"data/{structure_id}.json"                                 # 従来のパス（後方互換性）
    ]
    
    logger.info(f"📂 構成ファイル読み込み開始: {structure_id}")
    logger.debug(f"  -> DATA_DIR: {get_data_dir()}")
    
    for path in possible_paths:
        logger.debug(f"  -> 試行パス: {path}")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    structure = json.load(f)
                logger.info(f"  ✅ 成功: {path}")
                return structure
            except json.JSONDecodeError as e:
                logger.error(f"  ❌ JSONデコードエラー: {path} - {e}")
                continue  # 次の候補へ
            except Exception as e:
                logger.error(f"  ❌ ファイル読み込みエラー: {path} - {e}")
                continue  # 次の候補へ
        else:
            logger.debug(f"  -> ファイルなし")

    logger.warning(f"⚠️ 構成ファイルが見つかりませんでした: {structure_id}")
    logger.warning(f"   確認した全パス: {possible_paths}")
    return None

def load_previous_version(structure_id: str) -> Optional[Dict[str, Any]]:
    """Load the previous version of a structure"""
    history_path = get_history_path(structure_id)
    if not os.path.exists(history_path):
        return None

    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    if not history:
        return None

    return history[-2] if len(history) >= 2 else history[-1]

def append_structure_log(structure: Dict[str, Any], action: str, detail: str = "") -> None:
    """Append a log entry to a structure's history"""
    now = datetime.now().isoformat()

    # Convert content to string for snapshot
    snapshot_content = (
        json.dumps(structure["content"], ensure_ascii=False, indent=2)
        if isinstance(structure.get("content"), dict)
        else structure.get("content", "")
    )

    log_entry = {
        "timestamp": now,
        "action": action,
        "detail": detail,
        "snapshot": {
            "content": snapshot_content,
            "title": structure.get("title", ""),
            "description": structure.get("description", "")
        }
    }

    if "history" not in structure:
        structure["history"] = []

    structure["history"].append(log_entry)

def get_candidates_for_evolution(threshold: float = 0.85) -> List[Dict[str, Any]]:
    """Get structures that need evolution (not final and low score)"""
    candidates = []
    for root, dirs, files in os.walk(get_data_dir()):
        for filename in files:
            if not filename.endswith(".json") or '_history' in filename:
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not data.get("is_final", False):
                        if data.get("intent_match", 1.0) < threshold:
                            candidates.append(data)
            except Exception as e:
                logger.error(f"読み込み失敗: {filename} → {e}")
    return candidates

def summarize_structure(structure: Dict[str, Any]) -> str:
    """Get a summary of a structure"""
    title = structure.get("title", "(タイトルなし)")
    desc = structure.get("description", "(説明なし)")
    return f"構成名：{title}\n説明：{desc}"

def summarize_user_requirements(chat_history: List[Dict[str, Any]]) -> str:
    """Summarize user requirements from chat history"""
    seen = set()
    user_ideas = []
    for m in chat_history:
        if m.get("role") == "user":
            content = m.get("content", "").strip()
            if len(content) >= 6 and content not in seen:
                user_ideas.append(content)
                seen.add(content)

    summary = "\n".join(f"- {idea}" for idea in user_ideas[-5:])  # Show last 5 items
    return summary if summary else "（まだ十分な要件が集まっていません）"

def normalize_structure_for_pages(content: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize structure content for pages"""
    def is_nested_dict(d: Dict[str, Any]) -> bool:
        return isinstance(d, dict) and any(isinstance(v, dict) for v in d.values())

    def to_snake_case(text: str) -> str:
        return re.sub(r'\W+', '_', text.lower()).strip('_')

    def generate_field(label: str, value: Any) -> Dict[str, Any]:
        return {
            "label": label,
            "name": to_snake_case(label) + "_" + str(uuid.uuid4())[:4],
            "type": "text",
            "value": value
        }

    pages = []
    if isinstance(content, dict):
        for page_key, page_val in content.items():
            page = {
                "title": re.sub(r"^\d+\.?\s*", "", page_key),
                "sections": []
            }
            if isinstance(page_val, dict):
                for section_key, section_val in page_val.items():
                    section = {
                        "title": re.sub(r"^\d+\.?\d*\s*", "", section_key),
                        "fields": []
                    }
                    if isinstance(section_val, dict):
                        for field_key, field_val in section_val.items():
                            section["fields"].append(generate_field(field_key, field_val))
                    else:
                        section["fields"].append(generate_field("説明", section_val))
                    page["sections"].append(section)
            else:
                section = {
                    "title": "概要",
                    "fields": [generate_field("説明", page_val)]
                }
                page["sections"].append(section)
            pages.append(page)

    return {
        "sections": pages,
        "pages": pages
    }

def ensure_json_string(structure: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure structure content is a JSON string"""
    if isinstance(structure.get("content"), dict):
        structure["content"] = json.dumps(structure["content"], ensure_ascii=False, indent=2)
    return structure

def update_structure_content(original: str, updates: list[dict]) -> str:
    """
    構成の内容を更新する（仮実装）
    :param original: JSON文字列
    :param updates: 差分のリスト（各要素に pattern, replacement がある）
    :return: 修正後のJSON文字列
    """
    import re
    for update in updates:
        pattern = update["pattern"]
        replacement = update["replacement"]
        original = re.sub(pattern, replacement, original, flags=re.DOTALL)
    return original

def validate_structure(structure: Union[Dict[str, Any], str]) -> Tuple[bool, List[str]]:
    """
    構成データのバリデーションを行う
    
    Args:
        structure (Union[Dict[str, Any], str]): バリデーション対象の構成データ（辞書またはJSON文字列）
        
    Returns:
        Tuple[bool, List[str]]: (バリデーション結果, エラーメッセージのリスト)
    """
    errors = []
    
    try:
        # JSON文字列の場合は辞書に変換
        if isinstance(structure, str):
            try:
                structure = json.loads(structure)
            except json.JSONDecodeError as e:
                errors.append(f"JSONの解析に失敗しました: {str(e)}")
                return False, errors
        
        # 必須フィールドのチェック
        required_fields = ["title", "description", "content"]
        for field in required_fields:
            if field not in structure:
                errors.append(f"必須フィールド '{field}' が存在しません")
        
        # フィールドの型チェック
        if "title" in structure and not isinstance(structure["title"], str):
            errors.append("'title' は文字列である必要があります")
        if "description" in structure and not isinstance(structure["description"], str):
            errors.append("'description' は文字列である必要があります")
        if "content" in structure and not isinstance(structure["content"], (dict, str)):
            errors.append("'content' は辞書または文字列である必要があります")
        
        # contentが文字列の場合はJSONとしてパース可能かチェック
        if isinstance(structure.get("content"), str):
            try:
                json.loads(structure["content"])
            except json.JSONDecodeError:
                errors.append("'content' のJSONパースに失敗しました")
        
        # 正規化を試みる（エラーチェックの一環として）
        try:
            normalized = normalize_structure_format(structure)
            if not normalized:
                errors.append("構成の正規化に失敗しました")
        except Exception as e:
            errors.append(f"構成の正規化中にエラーが発生しました: {str(e)}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        logger.error(f"バリデーション中に予期せぬエラーが発生しました: {str(e)}")
        errors.append(f"予期せぬエラー: {str(e)}")
        return False, errors 

def normalize_structure_format(structure: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    構成データを正規化する
    
    Args:
        structure (Union[Dict[str, Any], str]): 正規化対象の構成データ（辞書またはJSON文字列）
        
    Returns:
        Dict[str, Any]: 正規化された構成データ
        
    Raises:
        ValueError: 正規化に失敗した場合
    """
    try:
        # JSON文字列の場合は辞書に変換
        if isinstance(structure, str):
            try:
                structure = json.loads(structure)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSONの解析に失敗しました: {str(e)}")
        
        # 基本的な構造を確保
        normalized = {
            "title": structure.get("title", "Untitled"),
            "description": structure.get("description", ""),
            "content": structure.get("content", {}),
            "metadata": structure.get("metadata", {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # contentが文字列の場合はJSONとしてパース
        if isinstance(normalized["content"], str):
            try:
                normalized["content"] = json.loads(normalized["content"])
            except json.JSONDecodeError:
                normalized["content"] = {"raw": normalized["content"]}
        
        # sections → pages 形式の統一
        if "sections" in normalized["content"]:
            normalized["content"] = normalize_structure_for_pages(normalized["content"])
        
        # Noneや空文字の削除
        def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            return {
                k: clean_dict(v) if isinstance(v, dict) else v
                for k, v in d.items()
                if v is not None and v != ""
            }
        
        normalized["content"] = clean_dict(normalized["content"])
        
        return normalized
        
    except Exception as e:
        logger.error(f"構成の正規化中にエラーが発生しました: {str(e)}")
        raise ValueError(f"構成の正規化に失敗しました: {str(e)}")

def load_structure(structure_id: str) -> Dict[str, Any]:
    """
    指定されたIDの構造データを読み込む
    
    Args:
        structure_id (str): 読み込む構造データのID
        
    Returns:
        Dict[str, Any]: 読み込んだ構造データ
        
    Raises:
        FileNotFoundError: 構造データファイルが見つからない場合
        json.JSONDecodeError: JSONの解析に失敗した場合
        ValueError: その他のエラーが発生した場合
    """
    try:
        # 構造データファイルのパスを取得
        structure_path = get_structure_path(structure_id)
        
        # ファイルが存在しない場合はエラー
        if not os.path.exists(structure_path):
            raise FileNotFoundError(f"構造データファイルが見つかりません: {structure_path}")
        
        # ファイルを読み込む
        with open(structure_path, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        
        # 構造データを正規化
        return normalize_structure_format(structure)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSONの解析に失敗しました: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"構造データの読み込み中にエラーが発生しました: {str(e)}")
        raise ValueError(f"構造データの読み込みに失敗しました: {str(e)}")

def is_ui_ready(structure: dict) -> bool:
    """
    構成がUI出力に適しているかどうかを判定する
    
    Args:
        structure: 構成データ
        
    Returns:
        bool: UI出力に適している場合はTrue
    """
    content = structure.get("content", {})
    
    # contentが文字列の場合（HTMLが直接含まれている場合）
    if isinstance(content, str):
        return "<div" in content or "<html" in content or "UI" in content or "画面構成" in content
    
    # contentが辞書の場合（構造化データ）
    if isinstance(content, dict):
        # タイトルや説明にUI関連のキーワードが含まれているかチェック
        title = str(content.get("title", "")).lower()
        description = str(content.get("description", "")).lower()
        
        ui_keywords = [
            "ui", "画面", "インターフェース", "プレビュー", "表示", 
            "コンポーネント", "レイアウト", "デザイン", "スタイル",
            "html", "css", "javascript", "react", "vue", "angular"
        ]
        
        # タイトルまたは説明にUI関連キーワードが含まれているかチェック
        for keyword in ui_keywords:
            if keyword in title or keyword in description:
                return True
        
        # content内の構成要素をチェック
        content_elements = content.get("content", {})
        if isinstance(content_elements, dict):
            for key, value in content_elements.items():
                key_lower = str(key).lower()
                if any(keyword in key_lower for keyword in ui_keywords):
                    return True
                
                # 値が文字列でHTMLタグが含まれている場合
                if isinstance(value, str) and ("<div" in value or "<html" in value):
                    return True
    
    return False

__all__ = [
    'StructureDict',
    'StructureHistory',
    'get_structure_path',
    'get_history_path',
    'get_structure',
    'save_structure',
    'get_structure_history',
    'save_structure_history',
    'load_structures',
    'load_structure',
    'load_previous_version',
    'append_structure_log',
    'get_candidates_for_evolution',
    'summarize_structure',
    'summarize_user_requirements',
    'normalize_structure_format',
    'validate_structure',
    'is_ui_ready'
] 