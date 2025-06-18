"""
Flaskアプリケーションのエントリーポイント
"""

from flask import Flask
from routes.edit_routes import edit_bp

def create_app() -> Flask:
    """Flaskアプリケーションを作成して返す"""
    app = Flask(__name__)
    
    # ブループリントの登録
    app.register_blueprint(edit_bp, url_prefix='/api/edit')
    
    return app 