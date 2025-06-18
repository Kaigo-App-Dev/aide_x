"""
Flaskアプリケーションのエントリーポイント
"""

from flask import Flask
from src.routes.edit_routes import edit_bp

def create_app() -> Flask:
    """Flaskアプリケーションを作成して返す"""
    app = Flask(__name__)
    
    # ここでのBlueprint登録は削除（main.pyでregister_routes(app)を使うため）
    # app.register_blueprint(edit_bp, url_prefix='/api/edit')
    
    return app 