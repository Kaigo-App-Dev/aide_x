from flask import Flask, redirect, request
from dotenv import load_dotenv
import os

from routes import chat, structure
from routes.evolve import evolve_bp
from routes.preview import preview_bp
from routes.structure import structure_bp

# 環境変数読み込み（APIキーなど）
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "default_secret")

    # Blueprint登録
    app.register_blueprint(chat.chat_bp)
    app.register_blueprint(structure.structure_bp)
    app.register_blueprint(evolve_bp)
    app.register_blueprint(preview_bp)

    # トップページルート
    @app.route('/')
    def index():
        return redirect('/structure/list')

    # ✅ 軽量ログ出力：アクセス内容を明示的に表示
    @app.before_request
    def log_request():
        print(f"➡️ {request.method} {request.path}", flush=True)

    return app

# __main__ 実行ブロック（ログ設定＋起動）
import logging
from werkzeug.serving import WSGIRequestHandler

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )

    logging.getLogger('werkzeug').setLevel(logging.DEBUG)

    app = create_app()
    with app.app_context():
        print("🔍 登録ルート一覧：")
        for rule in app.url_map.iter_rules():
            print(rule)

    print("🚀 ローカルサーバー起動: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)

# ✅ Flask CLI 用のグローバル変数定義（必要に応じて使用）
app = create_app()
