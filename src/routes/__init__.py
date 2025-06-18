"""
Routes package for the application.
"""

from flask import Flask
from .base_routes import base_bp
from .preview_routes import preview_bp

def register_routes(app: Flask) -> None:
    """
    FlaskアプリケーションにBlueprintを登録する

    Args:
        app (Flask): Flaskアプリケーションインスタンス
    """
    app.register_blueprint(base_bp)
    app.register_blueprint(preview_bp) 