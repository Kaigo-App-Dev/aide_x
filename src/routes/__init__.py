"""
Routes package for the application.
"""

from flask import Flask
from .base_routes import base_bp
from .preview_routes import preview_bp
from .edit_routes import edit_bp
from .unified_routes import unified_bp
from .logs_routes import logs_bp

def register_routes(app: Flask) -> None:
    """
    FlaskアプリケーションにBlueprintを登録する

    Args:
        app (Flask): Flaskアプリケーションインスタンス
    """
    app.register_blueprint(base_bp)
    app.register_blueprint(preview_bp)
    app.register_blueprint(edit_bp)
    app.register_blueprint(unified_bp)
    app.register_blueprint(logs_bp)
    
    print("✅ ルート登録完了:")
    print(f"   - base_bp: {base_bp.url_prefix}")
    print(f"   - preview_bp: {preview_bp.url_prefix}")
    print(f"   - edit_bp: {edit_bp.url_prefix}")
    print(f"   - unified_bp: {unified_bp.url_prefix}")
    print(f"   - logs_bp: {logs_bp.url_prefix}") 