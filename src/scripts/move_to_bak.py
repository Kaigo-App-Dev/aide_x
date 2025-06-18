#!/usr/bin/env python
"""
不要ファイルを.bakディレクトリに退避するスクリプト

このスクリプトは、指定されたファイルとディレクトリを.bakディレクトリに移動します。
元のディレクトリ構造を保持しながら、ファイルを退避します。
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 退避対象のファイルとディレクトリ
TARGETS = [
    "utils/openai_utils.py",
    "utils/nl2br.py",
    "tests/conftest_backup.py",
    "tests/test_minimal.py",
    "test_output.log",
    "app.log",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache"
]

def ensure_bak_dir() -> Path:
    """
    .bakディレクトリが存在することを確認し、必要に応じて作成します。
    
    Returns:
        Path: .bakディレクトリのパス
    """
    bak_dir = Path(".bak")
    if not bak_dir.exists():
        logger.info("Creating .bak directory")
        bak_dir.mkdir()
    return bak_dir

def move_to_bak(target: str, bak_dir: Path, overwrite: bool = True) -> bool:
    """
    指定されたファイルまたはディレクトリを.bakディレクトリに移動します。
    
    Args:
        target (str): 移動対象のパス
        bak_dir (Path): .bakディレクトリのパス
        overwrite (bool): 既存ファイルを上書きするかどうか
        
    Returns:
        bool: 移動が成功したかどうか
    """
    source = Path(target)
    if not source.exists():
        logger.warning(f"Source does not exist: {target}")
        return False
    
    # 退避先のパスを構築（元のディレクトリ構造を保持）
    dest = bak_dir / target
    
    # 親ディレクトリが存在することを確認
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if dest.exists():
            if not overwrite:
                logger.info(f"Skipping existing file: {target}")
                return False
            if dest.is_file():
                dest.unlink()
            else:
                shutil.rmtree(dest)
        
        if source.is_file():
            shutil.copy2(source, dest)
            source.unlink()
            logger.info(f"Moved file: {target}")
        else:
            shutil.copytree(source, dest)
            shutil.rmtree(source)
            logger.info(f"Moved directory: {target}")
        
        return True
    except Exception as e:
        logger.error(f"Error moving {target}: {str(e)}")
        return False

def main():
    """メイン関数"""
    logger.info("Starting file backup process")
    
    # .bakディレクトリの確認
    bak_dir = ensure_bak_dir()
    
    # 各ターゲットの移動
    success_count = 0
    for target in TARGETS:
        if move_to_bak(target, bak_dir):
            success_count += 1
    
    logger.info(f"Backup process completed. {success_count}/{len(TARGETS)} files moved successfully.")

if __name__ == "__main__":
    main() 