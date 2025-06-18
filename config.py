import os
from dotenv import load_dotenv
from datetime import timedelta

# 環境変数の読み込み
load_dotenv()

class Config:
    """基本設定クラス"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    TESTING = False
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    
    # アプリケーション固有の設定
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    if not ANTHROPIC_API_KEY:
        raise ValueError("❌ ANTHROPIC_API_KEY が .env に存在しません。設定を確認してください。")
    
    # セッション設定
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30分
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # データベース設定
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS設定
    ENABLE_CORS = False
    
    # セキュリティ設定
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    
    # アプリケーション設定
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # その他の設定
    TEMPLATES_AUTO_RELOAD = True
    
    @staticmethod
    def init_app(app):
        """アプリケーション初期化時の追加設定"""
        # アップロードフォルダの作成
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # ロギング設定の適用
        app.logger.setLevel(Config.LOG_LEVEL)
        
        # ファイルハンドラーの設定
        if not app.debug:
            import logging
            from logging.handlers import RotatingFileHandler
            
            # ログディレクトリの作成
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # ログファイルの設定
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=1024 * 1024,  # 1MB
                backupCount=10,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
            app.logger.addHandler(file_handler)
            
            # エラーログの設定
            error_file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'error.log'),
                maxBytes=1024 * 1024,  # 1MB
                backupCount=10,
                encoding='utf-8'
            )
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
            app.logger.addHandler(error_file_handler)

class DevelopmentConfig(Config):
    """開発環境用設定"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        # 開発環境特有の設定
        app.config['TEMPLATES_AUTO_RELOAD'] = True

class TestingConfig(Config):
    """テスト環境用設定"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    WTF_CSRF_ENABLED = False  # テスト時のCSRF保護を無効化
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'  # テスト用インメモリデータベース

class ProductionConfig(Config):
    """本番環境用設定"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        # 本番環境特有の設定
        # 例: セキュリティヘッダーの設定
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['REMEMBER_COOKIE_SECURE'] = True
        app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# 環境設定の辞書
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """環境変数から適切な設定を取得"""
    env = os.getenv('FLASK_ENV', 'default')
    return config.get(env, config['default']) 