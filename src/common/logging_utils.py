"""
ログ設定ユーティリティ

このモジュールは、アプリケーション全体で使用するログ設定を提供します。
"""

import logging
import os
import sys
import traceback
from typing import Optional


def setup_logging(
    log_file: str = "app.log",
    log_level: str = "INFO",
    debug_mode: Optional[bool] = None
) -> logging.Logger:
    """
    ログ設定を初期化する
    
    Args:
        log_file: ログファイルのパス（デフォルト: "app.log"）
        log_level: ログレベル（デフォルト: "INFO"）
        debug_mode: デバッグモード（Noneの場合は環境変数FLASK_DEBUGから取得）
    
    Returns:
        logging.Logger: 設定されたルートロガー
    """
    # デバッグモードの取得
    if debug_mode is None:
        debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    # ログレベルの取得
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # ルートロガー（logging.getLogger("root")）を使って一元出力
    root_logger = logging.getLogger("root")
    root_logger.setLevel(level)
    root_logger.handlers.clear()  # 重複登録を防ぐ
    
    # ログフォーマッター（詳細版）
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    
    # シンプルフォーマッター
    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    
    # ファイルハンドラーを標準として追加（app.log）
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG)  # ファイルにはすべてのログを出力
    root_logger.addHandler(file_handler)
    
    # コンソールハンドラー（常に出力）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Flask関連のログレベルを調整
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # デバッグ用：設定確認
    root_logger.info(f"🔍 setup_logging() - root.handlers: {len(root_logger.handlers)}")
    root_logger.info(f"🔍 setup_logging() - root.level: {root_logger.level}")
    root_logger.info(f"🔍 setup_logging() - FLASK_DEBUG: {debug_mode}")
    root_logger.info(f"🔍 setup_logging() - log_file: {os.path.abspath(log_file)}")
    
    # ログ初期化完了の確認
    root_logger.info("✅ ログ初期化完了")
    
    return root_logger


def get_logger(name: str = "root") -> logging.Logger:
    """
    ロガーを取得する（setup_logging()実行後の使用を想定）
    
    Args:
        name: ロガー名（デフォルト: "root"）
    
    Returns:
        logging.Logger: 指定されたロガー
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, error: Exception, context: str = ""):
    """
    例外をログに出力する（traceback付き）
    
    Args:
        logger: ロガー
        error: 例外オブジェクト
        context: エラーが発生したコンテキスト
    """
    logger.error(f"❌ 例外発生 - {context}: {str(error)}")
    logger.error(f"📋 例外詳細:\n{traceback.format_exc()}")
    
    # 標準出力にも出力（デバッグ用）
    print(f"❌ 例外発生 - {context}: {str(error)}")
    print(f"📋 例外詳細:")
    traceback.print_exc()


def log_request(logger: logging.Logger, request, context: str = ""):
    """
    リクエスト情報をログに出力する
    
    Args:
        logger: ロガー
        request: Flaskリクエストオブジェクト
        context: コンテキスト情報
    """
    logger.info(f"📥 リクエスト受信 - {context}")
    logger.debug(f"📋 メソッド: {request.method}")
    logger.debug(f"📋 URL: {request.url}")
    logger.debug(f"📋 ヘッダー: {dict(request.headers)}")
    
    if request.method == 'POST':
        try:
            if request.is_json:
                logger.debug(f"📋 JSONデータ: {request.get_json()}")
            else:
                logger.debug(f"📋 フォームデータ: {dict(request.form)}")
        except Exception as e:
            logger.warning(f"⚠️ リクエストデータ取得エラー: {str(e)}") 