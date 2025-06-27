"""
Flaskアプリケーションのエントリーポイント
"""

import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect

# logging_utilsを最初にインポートして設定を適用
from src.common.logging_utils import setup_logging, get_logger

# ログ設定をアプリケーションの起動時に実行
LOG_LEVEL = "DEBUG" if os.getenv("FLASK_DEBUG") == "1" else "INFO"
setup_logging(log_level=LOG_LEVEL)

from src.routes import register_routes
from src.routes.edit_routes import edit_bp

# ルートロガーを取得
logger = get_logger("app")

def create_app() -> Flask:
    """Flaskアプリケーションを作成して返す"""
    logger.info("🚀 Flaskアプリケーション作成開始...")
    
    # プロジェクトルートディレクトリを取得
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')
    
    # テンプレートフォルダの存在確認
    if not os.path.exists(template_folder):
        logger.warning(f"⚠️ 警告: テンプレートフォルダが見つかりません: {template_folder}")
    else:
        logger.info(f"✅ テンプレートフォルダを検出: {template_folder}")
    
    # 静的ファイルフォルダの存在確認
    if not os.path.exists(static_folder):
        logger.warning(f"⚠️ 警告: 静的ファイルフォルダが見つかりません: {static_folder}")
    else:
        logger.info(f"✅ 静的ファイルフォルダを検出: {static_folder}")
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    # セキュリティ設定
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-for-csrf')
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # ルートを登録
    register_routes(app)
    
    logger.info("✅ Flaskアプリケーション作成完了")
    return app

if __name__ == "__main__":
    app = create_app()
    # デバッグモードは環境変数 `FLASK_DEBUG=1` で制御
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")

# テスト用にappインスタンスをエクスポート
app = create_app() 