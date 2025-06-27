"""
AIDE-X メインアプリケーション

このモジュールは、AIDE-Xのメインアプリケーションを提供します。
Flaskアプリケーションの初期化、ルートの登録、エラーハンドリングを行います。
"""

from dotenv import load_dotenv
load_dotenv()  # .envファイルの読み込みを保証

import logging
import sys
import os

# 共通ログ設定ユーティリティからインポート
from src.common.logging_utils import setup_logging, get_logger

# Flaskアプリ生成前にログ設定を実行
setup_logging()

from flask import Flask, redirect, url_for, request, render_template, jsonify, flash, send_from_directory
from routes.chat.chat import chat_bp
from routes.structure.base_routes import structure_bp
from routes.evolve import evolve_bp
from src.routes.edit_routes import edit_bp
from flask_cors import CORS
import json
from datetime import datetime
from src.preview import render_html_from_structure
from src.text import structure_to_text
from config import get_config
from extensions import init_extensions
from error_handlers import register_error_handlers
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from src.llm.prompts.manager import PromptManager
from src.llm.prompts.prompt_loader import register_all_yaml_templates
from src.llm.controller import AIController
from src.llm.providers import ChatGPTProvider, ClaudeProvider, GeminiProvider
from src.routes import register_routes
from src.config.config import Config
from src.exceptions import AIProviderError, APIRequestError, ResponseFormatError
from typing import Dict, Any, Optional, List

# アプリケーション設定
FLASK_DEBUG = False  # デバッグモードを無効化
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1")

# 環境変数の確認
logger = get_logger("root")
logger.info("🔧 環境設定:")
logger.info(f"FLASK_DEBUG={FLASK_DEBUG}")
logger.info(f"LOG_LEVEL={LOG_LEVEL}")
logger.info(f"GEMINI_API_KEY={'設定済み' if GEMINI_API_KEY else '未設定'}")
logger.info(f"GEMINI_API_BASE={GEMINI_API_BASE}")

# Gemini APIのバージョン確認
if "v1beta" in GEMINI_API_BASE:
    logger.warning("⚠️ 警告: GEMINI_API_BASEにv1betaが含まれています。v1に更新してください。")
else:
    logger.info("[OK] Gemini APIバージョン: v1")

# 環境変数から設定を取得
config = get_config()

def create_app():
    """Flaskアプリケーションの作成と設定"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 拡張機能の初期化（CSRF、DB、認証など）
    init_extensions(app)
    
    # プロンプトマネージャーの初期化
    prompt_manager = PromptManager()
    
    # テンプレートの登録
    from src.llm.prompts.templates import register_all_templates
    register_all_templates(prompt_manager)
    register_all_yaml_templates(prompt_manager)
    logger.info("PromptManager initialized and templates registered")
    
    # AIプロバイダーの初期化
    chatgpt_provider = ChatGPTProvider(prompt_manager=prompt_manager)
    claude_provider = ClaudeProvider(prompt_manager=prompt_manager)
    gemini_provider = GeminiProvider(prompt_manager=prompt_manager)
    logger.info("AI providers initialized")
    
    # AIコントローラーの初期化
    ai_controller = AIController(prompt_manager)
    logger.info("AI controller initialized")
    
    # CORSの設定
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # ルートの登録
    register_routes(app)
    
    # ログテスト用ルート
    @app.route("/log-test")
    def log_test():
        logger.info("✅ /log-test - アクセス成功")
        logger.info("🧪 logger(root) - アクセス成功")
        return "OK - アクセスログテスト完了", 200
    
    # CSRFエラーハンドリング
    from flask_wtf.csrf import CSRFError
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.error('CSRF error: %s', str(e))
        return render_template("errors/csrf_error.html", reason=e.description), 400
    
    # アクセスログの明示的出力（werkzeugロガーに依存しない）
    @app.before_request
    def log_access_info():
        logger.info(f"[ACCESS] {request.method} {request.path} from {request.remote_addr}")
    
    # レスポンスログ（オプション）
    @app.after_request
    def log_response_info(response):
        logger.info(f"[RESPONSE] {request.method} {request.path} -> {response.status_code}")
        return response
    
    # エラーハンドリング
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error('Unhandled error: %s', str(error), exc_info=True)
        return jsonify({
            'error': str(error),
            'type': error.__class__.__name__
        }), 500
    
    return app

# ローカル実行ブロック
if __name__ == '__main__':
    logger.info("🚀 Flaskサーバーを起動します")
    app = create_app()
    with app.app_context():
        logger.info("🚀 ローカルサーバー起動: http://127.0.0.1:5000")
    
    # debug=Falseで起動（デバッグモードを無効化）
    app.run(
        debug=False,  # デバッグモードを無効化
        host='127.0.0.1',
        port=5000,
        use_reloader=False  # リローダーを無効にしてstdoutキャプチャの問題を回避
    )
