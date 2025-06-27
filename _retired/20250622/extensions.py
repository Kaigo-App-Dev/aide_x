import os
import sys
import io
from typing import Optional, Any, Dict
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

# 標準出力のエンコーディングをUTF-8に設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# データベース
db = SQLAlchemy()
migrate = Migrate()

# 認証
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # type: ignore  # ログインが必要なページにアクセスした際のリダイレクト先
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
login_manager.login_message_category = 'info'

# セキュリティ
csrf = CSRFProtect()

# CORS
cors = CORS()

def init_extensions(app: Flask) -> None:
    """Flaskアプリケーションの初期化
    
    注意: ログ設定はmain.pyのsetup_logging()関数で一元管理されます。
    この関数ではログ設定は行いません。
    """
    
    # データベースの設定（SQLAlchemy初期化前に設定）
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///app.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # セッションの設定
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-very-secure-key-change-in-production")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800  # 30分
    
    # 拡張機能の初期化
    db.init_app(app)
    migrate.init_app(app, db)

    # 認証の初期化
    login_manager.init_app(app)

    # セキュリティの初期化
    csrf.init_app(app)

    # CORSの初期化（必要な場合のみ）
    if app.config.get('ENABLE_CORS', False):
        cors.init_app(app)

    # ユーザーローダーの設定
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User  # 循環インポートを避けるため、ここでインポート
        return User.query.get(int(user_id))

    # アップロードの設定
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True) 