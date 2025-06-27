from flask import Blueprint, render_template

# Blueprintの定義
structure_bp = Blueprint("structure", __name__, url_prefix="/structure")

# ルートの定義
@structure_bp.route("/test")
def test_route():
    return "OK"

# base_routesのインポート（Blueprintの定義後にインポート）
from . import base_routes
from . import unified_routes

print("[OK] structure/__init__.py 読み込まれました")
