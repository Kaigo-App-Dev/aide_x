"""
構造履歴管理モジュール

このモジュールは、構造の評価・補完・保存操作の履歴を管理します。
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

def get_data_dir() -> str:
    """データディレクトリを取得（環境変数AIDEX_DATA_DIRを優先）"""
    return os.environ.get('AIDEX_DATA_DIR', 'data')

def save_structure_history(
    structure_id: str, 
    role: str, 
    source: str, 
    content: str, 
    module_id: str = ""
) -> bool:
    """
    構造履歴を保存する
    
    Args:
        structure_id (str): 構造ID
        role (str): 操作者の役割（user, claude, gemini等）
        source (str): 操作の種類（save_structure, structure_evaluation, structure_completion等）
        content (str): 保存する内容
        module_id (str): モジュールID（オプション）
        
    Returns:
        bool: 保存成功時True、失敗時False
    """
    try:
        # 履歴ディレクトリの作成
        data_dir = get_data_dir()
        history_path = Path(f"{data_dir}/history")
        history_path.mkdir(parents=True, exist_ok=True)
        
        # ファイルパスの設定
        file_path = history_path / f"{structure_id}.json"
        
        # 既存履歴を読み込み or 初期化
        if file_path.exists():
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"既存履歴ファイルの読み込みに失敗: {e}")
                data = _create_initial_history_data(structure_id, module_id)
        else:
            data = _create_initial_history_data(structure_id, module_id)
        
        # 新しい履歴エントリを追加
        history_entry = {
            "role": role,
            "source": source,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        data["history"].append(history_entry)
        
        # ファイルに保存
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[HISTORY] Saved: {structure_id} ({role}, {source})")
        return True
        
    except Exception as e:
        logger.error(f"履歴保存中にエラーが発生: {str(e)}")
        return False

def save_evaluation_completion_history(structure: Dict[str, Any]) -> bool:
    """
    Claude評価とGemini補完の履歴をJSON形式で永続化する
    
    Args:
        structure (Dict[str, Any]): 構造データ（evaluationsとcompletionsを含む）
        
    Returns:
        bool: 保存成功時True、失敗時False
    """
    try:
        structure_id = structure.get("id")
        if not structure_id:
            logger.error("構造IDがありません")
            return False
            
        # 保存先ディレクトリの作成
        history_dir = Path("logs/structure_history")
        history_dir.mkdir(parents=True, exist_ok=True)
        
        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{structure_id}_{timestamp}.json"
        file_path = history_dir / filename
        
        # 保存データの作成
        history_data = {
            "structure_id": structure_id,
            "timestamp": datetime.now().isoformat(),
            "evaluations": structure.get("evaluations", []),
            "completions": structure.get("completions", [])
        }
        
        # JSONファイルに保存
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ 評価・補完履歴を保存しました: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 評価・補完履歴保存中にエラーが発生: {str(e)}")
        return False

def load_evaluation_completion_history(structure_id: str) -> List[Dict[str, Any]]:
    """
    指定された構造IDの評価・補完履歴を読み込む
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        List[Dict[str, Any]]: 履歴データのリスト
    """
    try:
        history_dir = Path("logs/structure_history")
        if not history_dir.exists():
            return []
            
        # 構造IDで始まるファイルを検索
        history_files = list(history_dir.glob(f"{structure_id}_*.json"))
        history_files.sort(reverse=True)  # 新しい順
        
        histories = []
        for file_path in history_files:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    histories.append(history_data)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"履歴ファイルの読み込みに失敗: {file_path}, error: {e}")
                
        logger.info(f"📖 評価・補完履歴を読み込みました: {len(histories)}件")
        return histories
        
    except Exception as e:
        logger.error(f"❌ 評価・補完履歴読み込み中にエラーが発生: {str(e)}")
        return []

def _create_initial_history_data(structure_id: str, module_id: str = "") -> Dict[str, Any]:
    """
    初期履歴データを作成する
    
    Args:
        structure_id (str): 構造ID
        module_id (str): モジュールID
        
    Returns:
        Dict[str, Any]: 初期履歴データ
    """
    return {
        "structure_id": structure_id,
        "module_id": module_id,
        "timestamp": datetime.now().isoformat(),
        "history": []
    }

def load_structure_history(structure_id: str) -> Optional[Dict[str, Any]]:
    """
    構造履歴を読み込む
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        Optional[Dict[str, Any]]: 履歴データ、存在しない場合はNone
    """
    try:
        file_path = Path("data/history") / f"{structure_id}.json"
        if not file_path.exists():
            return None
            
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"履歴読み込み中にエラーが発生: {str(e)}")
        return None

def get_history_summary(structure_id: str) -> Dict[str, Any]:
    """
    構造履歴のサマリーを取得する
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        Dict[str, Any]: 履歴サマリー
    """
    history_data = load_structure_history(structure_id)
    if not history_data:
        return {
            "structure_id": structure_id,
            "total_entries": 0,
            "last_updated": None,
            "roles": [],
            "sources": []
        }
    
    history = history_data.get("history", [])
    roles = list(set(entry.get("role", "") for entry in history))
    sources = list(set(entry.get("source", "") for entry in history))
    
    return {
        "structure_id": structure_id,
        "total_entries": len(history),
        "last_updated": history[-1].get("timestamp") if history else None,
        "roles": roles,
        "sources": sources
    }

def cleanup_old_history(days_to_keep: int = 30) -> int:
    """
    古い履歴ファイルを削除する
    
    Args:
        days_to_keep (int): 保持する日数
        
    Returns:
        int: 削除されたファイル数
    """
    try:
        history_path = Path("data/history")
        if not history_path.exists():
            return 0
            
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in history_path.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"古い履歴ファイルを削除: {file_path}")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"履歴クリーンアップ中にエラーが発生: {str(e)}")
        return 0

def get_history_diff_data(structure_id: str, index: int = 0) -> Optional[Dict[str, Any]]:
    """
    指定されたインデックスの履歴データとその前の履歴との差分を取得する
    
    Args:
        structure_id (str): 構造ID
        index (int): 履歴のインデックス（0が最新）
        
    Returns:
        Optional[Dict[str, Any]]: 差分データ、存在しない場合はNone
    """
    try:
        # 履歴を読み込み
        histories = load_evaluation_completion_history(structure_id)
        if not histories:
            return None
            
        # インデックスの範囲チェック
        if index < 0 or index >= len(histories):
            return None
            
        current_history = histories[index]
        
        # 前の履歴を取得（存在する場合）
        previous_history = histories[index + 1] if index + 1 < len(histories) else None
        
        # 差分データの構築
        diff_data = {
            "current_content": current_history,
            "previous_content": previous_history,
            "timestamp": current_history.get("timestamp"),
            "source": "evaluation_completion",
            "index": index,
            "total_count": len(histories),
            "has_previous": previous_history is not None,
            "has_next": index > 0
        }
        
        logger.info(f"📊 履歴差分データを取得: {structure_id}, index={index}")
        return diff_data
        
    except Exception as e:
        logger.error(f"❌ 履歴差分データ取得中にエラーが発生: {str(e)}")
        return None

class StructureHistoryManager:
    """構成評価履歴の管理クラス"""
    
    def __init__(self, data_dir: str = "data/history"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_history_count = 50  # 履歴の最大保持件数
    
    def save_structure_history(self, structure_id: str, history_entry: Dict[str, Any]) -> bool:
        """
        構成評価履歴を保存する
        
        Args:
            structure_id: 構成ID
            history_entry: 履歴エントリ（timestamp, structure_before, structure_after, evaluation_result）
            
        Returns:
            bool: 保存成功時True
        """
        try:
            # タイムスタンプが設定されていない場合は現在時刻を設定
            if 'timestamp' not in history_entry:
                history_entry['timestamp'] = datetime.now().isoformat()
            
            # ファイルパス
            history_file = self.data_dir / f"{structure_id}.json"
            
            # 既存の履歴を読み込み
            existing_history = self.load_structure_history(structure_id)
            
            # 新しい履歴を追加
            existing_history.append(history_entry)
            
            # 履歴数が上限を超えた場合、古いものを削除
            if len(existing_history) > self.max_history_count:
                existing_history = existing_history[-self.max_history_count:]
                logger.info(f"履歴数が上限({self.max_history_count}件)を超えたため、古い履歴を削除しました")
            
            # JSONファイルに保存
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(existing_history, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"✅ 構成評価履歴を保存しました - structure_id: {structure_id}, 履歴数: {len(existing_history)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 構成評価履歴の保存に失敗しました - structure_id: {structure_id}, error: {str(e)}")
            return False
    
    def load_structure_history(self, structure_id: str) -> List[Dict[str, Any]]:
        """
        構成評価履歴を読み込む
        
        Args:
            structure_id: 構成ID
            
        Returns:
            List[Dict[str, Any]]: 履歴リスト（新しい順）
        """
        try:
            history_file = self.data_dir / f"{structure_id}.json"
            
            if not history_file.exists():
                logger.info(f"履歴ファイルが存在しません - {history_file}")
                return []
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # 新しい順にソート
            history_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            logger.info(f"✅ 構成評価履歴を読み込みました - structure_id: {structure_id}, 履歴数: {len(history_data)}")
            return history_data
            
        except Exception as e:
            logger.error(f"❌ 構成評価履歴の読み込みに失敗しました - structure_id: {structure_id}, error: {str(e)}")
            return []
    
    def get_history_summary(self, structure_id: str) -> Dict[str, Any]:
        """
        履歴のサマリー情報を取得
        
        Args:
            structure_id: 構成ID
            
        Returns:
            Dict[str, Any]: サマリー情報
        """
        history = self.load_structure_history(structure_id)
        
        if not history:
            return {
                'total_count': 0,
                'latest_timestamp': None,
                'providers': [],
                'average_score': None
            }
        
        # プロバイダー別の統計
        providers = {}
        scores = []
        
        for entry in history:
            eval_result = entry.get('evaluation_result', {})
            provider = eval_result.get('provider', 'unknown')
            
            if provider not in providers:
                providers[provider] = 0
            providers[provider] += 1
            
            # スコアの収集
            score = eval_result.get('score')
            if score is not None and isinstance(score, (int, float)):
                scores.append(score)
        
        return {
            'total_count': len(history),
            'latest_timestamp': history[0].get('timestamp') if history else None,
            'providers': list(providers.keys()),
            'provider_counts': providers,
            'average_score': sum(scores) / len(scores) if scores else None,
            'score_count': len(scores)
        }
    
    def delete_history(self, structure_id: str) -> bool:
        """
        指定された構成の履歴を削除
        
        Args:
            structure_id: 構成ID
            
        Returns:
            bool: 削除成功時True
        """
        try:
            history_file = self.data_dir / f"{structure_id}.json"
            
            if history_file.exists():
                history_file.unlink()
                logger.info(f"✅ 構成評価履歴を削除しました - structure_id: {structure_id}")
                return True
            else:
                logger.info(f"履歴ファイルが存在しません - structure_id: {structure_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 構成評価履歴の削除に失敗しました - structure_id: {structure_id}, error: {str(e)}")
            return False
    
    def cleanup_old_histories(self, days_to_keep: int = 30) -> int:
        """
        古い履歴ファイルを削除
        
        Args:
            days_to_keep: 保持する日数
            
        Returns:
            int: 削除したファイル数
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for history_file in self.data_dir.glob("*.json"):
                if history_file.stat().st_mtime < cutoff_time:
                    history_file.unlink()
                    deleted_count += 1
                    logger.info(f"古い履歴ファイルを削除しました: {history_file}")
            
            logger.info(f"✅ 古い履歴ファイルのクリーンアップ完了 - 削除数: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ 古い履歴ファイルのクリーンアップに失敗しました - error: {str(e)}")
            return 0

# グローバルインスタンス
history_manager = StructureHistoryManager()

def save_evaluation_history(structure_id: str, history_entry: Dict[str, Any]) -> bool:
    """評価履歴保存の簡易関数"""
    return history_manager.save_structure_history(structure_id, history_entry)

def load_evaluation_history(structure_id: str) -> List[Dict[str, Any]]:
    """評価履歴読み込みの簡易関数"""
    return history_manager.load_structure_history(structure_id)

def get_evaluation_history_summary(structure_id: str) -> Dict[str, Any]:
    """評価履歴サマリー取得の簡易関数"""
    return history_manager.get_history_summary(structure_id) 