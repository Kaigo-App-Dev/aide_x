"""
AIDE-X メインアプリケーション

このモジュールは、AIDE-Xのメインアプリケーションを提供します。
Flaskアプリケーションの初期化、ルートの登録、エラーハンドリングを行います。
"""

from dotenv import load_dotenv
load_dotenv()  # .envファイルの読み込みを保証

from flask import Flask, redirect, url_for, request, render_template, jsonify, flash, send_from_directory
import os
import logging
import sys
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
from logging.handlers import RotatingFileHandler
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
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1")

# 環境変数の確認
print("\n🔧 環境設定:")
print(f"FLASK_DEBUG={FLASK_DEBUG}")
print(f"LOG_LEVEL={LOG_LEVEL}")
print(f"GEMINI_API_KEY={'設定済み' if GEMINI_API_KEY else '未設定'}")
print(f"GEMINI_API_BASE={GEMINI_API_BASE}")

# Gemini APIのバージョン確認
if "v1beta" in GEMINI_API_BASE:
    print("⚠️ 警告: GEMINI_API_BASEにv1betaが含まれています。v1に更新してください。")
else:
    print("[OK] Gemini APIバージョン: v1")

# ログ設定
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 出力バッファのフラッシュ設定
sys.stdout.reconfigure(line_buffering=True)  # Python 3.7以上
sys.stderr.reconfigure(line_buffering=True)  # Python 3.7以上

# 標準出力のエンコーディングをUTF-8に設定（必要な場合のみ）

# 環境変数から設定を取得
config = get_config()

def create_app():
    """Flaskアプリケーションの作成と設定"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # プロンプトマネージャーの初期化
    prompt_manager = PromptManager()
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
    
    # リクエスト/レスポンスのロギング
    @app.before_request
    def log_request_info():
        logger.info('Headers: %s', request.headers)
        logger.info('Body: %s', request.get_data())
    
    @app.after_request
    def log_response_info(response):
        logger.info('Response: %s', response.get_data())
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
    app = create_app()
    with app.app_context():
        app.logger.info("🚀 ローカルサーバー起動: http://127.0.0.1:5000")
        sys.stdout.flush()  # 出力バッファをフラッシュ
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)

# Flask CLI用変数
app = create_app()

# 最後に追加
print("🔍 登録ルート一覧：")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")
