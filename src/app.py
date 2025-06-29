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
    
    # プロジェクトルートを取得
    root_dir = os.path.abspath(os.path.dirname(__file__) + "/..")
    static_dir = os.path.join(root_dir, "static")
    template_dir = os.path.join(root_dir, "templates")
    
    # テンプレートフォルダの存在確認
    if not os.path.exists(template_dir):
        logger.warning(f"⚠️ 警告: テンプレートフォルダが見つかりません: {template_dir}")
    else:
        logger.info(f"✅ テンプレートフォルダを検出: {template_dir}")
    
    # 静的ファイルフォルダの存在確認
    if not os.path.exists(static_dir):
        logger.warning(f"⚠️ 警告: 静的ファイルフォルダが見つかりません: {static_dir}")
    else:
        logger.info(f"✅ 静的ファイルフォルダを検出: {static_dir}")
    
    app = Flask(
        __name__,
        static_folder=static_dir,
        static_url_path='/static',
        template_folder=template_dir
    )
    
    # デバッグモードを有効にしてテンプレートキャッシュを無効化
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # セキュリティ設定
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-for-csrf')
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # ルートを登録
    register_routes(app)
    
    @app.route("/test-static")
    def test_static():
        return "Static endpoint OK"
    
    logger.info("✅ Flaskアプリケーション作成完了")
    return app

if __name__ == "__main__":
    app = create_app()
    # デバッグモードは環境変数 `FLASK_DEBUG=1` で制御
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=5000)

# テスト用にappインスタンスをエクスポート
app = create_app() 