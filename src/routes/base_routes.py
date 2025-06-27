"""
ベースルート定義モジュール
"""

from flask import Blueprint, jsonify, redirect, abort, url_for, render_template
import os
from pathlib import Path

base_bp = Blueprint('base', __name__)

@base_bp.route('/')
def index():
    """トップページ - 新規構成作成画面にリダイレクト"""
    return redirect(url_for("unified.new_unified_structure"))

@base_bp.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'ok',
        'message': 'Service is healthy'
    })

@base_bp.route('/structure/new')
def new_structure_placeholder():
    """新規構成作成の仮画面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>新規構成作成</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            .warning { color: #856404; background-color: #fff3cd; padding: 15px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>⚠ 新規構成作成</h2>
            <div class="warning">
                <p>現在、構成ファイルが存在しません。</p>
                <p>管理画面から新規構成を作成してください。</p>
            </div>
            <p><a href="/structure/list">構成一覧へ</a></p>
        </div>
    </body>
    </html>
    """

@base_bp.route('/help')
def help_page():
    """ヘルプページを表示"""
    return render_template('help.html')

@base_bp.route('/about')
def about_page():
    """バージョン情報ページを表示"""
    return render_template('about.html') 