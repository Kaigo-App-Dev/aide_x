import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def save_log(file_prefix: str, content: Dict[str, Any], category: str = "general") -> None:
    """
    ログを logs/<category>/YYYY-MM-DD/HHMMSS_<prefix>.json に保存する
    
    Args:
        file_prefix: ファイル名のプレフィックス（request/response/error）
        content: 保存するログ内容
        category: ログのカテゴリ（claude/gemini/chatgpt）
    """
    try:
        # タイムスタンプを追加
        content["timestamp"] = datetime.now().isoformat()
        
        # ログディレクトリの作成（YYYY-MM-DD形式）
        timestamp = datetime.now()
        date_dir = timestamp.strftime("%Y-%m-%d")
        log_dir = Path("logs") / category / date_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名の生成（HHMMSS_<prefix>.json形式）
        time_str = timestamp.strftime("%H%M%S")
        filename = f"{time_str}_{file_prefix}.json"
        filepath = log_dir / filename
        
        # JSONとして保存（UTF-8、インデント付き）
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.warning(f"Failed to save log file: {str(e)}")
        logger.warning(f"Category: {category}, Prefix: {file_prefix}")
        logger.warning(f"Content: {content}") 