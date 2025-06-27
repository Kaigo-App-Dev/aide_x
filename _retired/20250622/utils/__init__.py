"""
AIDE-X utils package
"""

from pathlib import Path

# プロジェクトのルートディレクトリを設定
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# ロガーの設定
import logging
logger = logging.getLogger(__name__)

def get_history_path(user_id: str) -> Path:
    """ユーザーの履歴ファイルパスを取得"""
    return DATA_DIR / f"history_{user_id}.json" 