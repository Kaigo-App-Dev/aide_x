"""
ロギングユーティリティ

このモジュールは、ログの保存と管理に関する機能を提供します。
"""

import logging
import os
from datetime import datetime
from typing import Optional

def save_log(message: str, level: str = "INFO", filename: Optional[str] = None) -> None:
    """
    ログメッセージを保存する
    
    Args:
        message (str): ログメッセージ
        level (str): ログレベル（"INFO", "WARNING", "ERROR", "DEBUG"）
        filename (Optional[str]): ログファイル名（指定しない場合は自動生成）
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"log_{timestamp}.txt"
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, filename)
    
    # ロガーの設定
    logger = logging.getLogger("aide_x")
    logger.setLevel(logging.DEBUG)
    
    # ファイルハンドラの設定
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # フォーマッタの設定
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    
    # ハンドラの追加
    logger.addHandler(file_handler)
    
    # ログレベルの設定
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # ログの出力
    logger.log(log_level, message)
    
    # ハンドラの削除（重複を防ぐため）
    logger.removeHandler(file_handler)

__all__ = ['save_log'] 