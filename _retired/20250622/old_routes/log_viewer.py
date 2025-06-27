"""
ログビューアーWeb UI

このモジュールは、Webブラウザからログファイルを検索・絞り込みできる機能を提供します。
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.tools.log_inspector import LogInspector
from src.common.logging_utils import get_logger

logger = get_logger("root")

log_viewer_bp = Blueprint('log_viewer', __name__, url_prefix='/logs')

@log_viewer_bp.route('/')
@login_required
def index():
    """ログビューアーのメインページ"""
    return render_template('log_viewer/index.html')

@log_viewer_bp.route('/search', methods=['POST'])
@login_required
def search_logs():
    """ログ検索API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "リクエストデータがありません"}), 400
        
        # 検索条件を取得
        structure_id = data.get('structure_id', '').strip()
        user_id = data.get('user_id', '').strip()
        level = data.get('level', '').strip()
        start_date = data.get('start_date', '').strip()
        end_date = data.get('end_date', '').strip()
        keyword = data.get('keyword', '').strip()
        limit = data.get('limit', 100)  # デフォルト100件
        
        # ログインスペクターを初期化
        inspector = LogInspector('app.log')
        
        # ログファイルを読み込み
        if not inspector.load_logs():
            return jsonify({"error": "ログファイルの読み込みに失敗しました"}), 500
        
        # フィルタリング
        filtered_logs = inspector.log_entries
        
        if structure_id:
            filtered_logs = inspector.filter_by_structure_id(structure_id)
        
        if user_id:
            filtered_logs = inspector.filter_by_user_id(user_id)
        
        if level:
            filtered_logs = inspector.filter_by_level(level)
        
        if start_date and end_date:
            filtered_logs = inspector.filter_by_date_range(start_date, end_date)
        
        if keyword:
            filtered_logs = inspector.filter_by_keyword(keyword)
        
        # 件数制限
        if limit and limit > 0:
            filtered_logs = filtered_logs[-limit:]
        
        # 統計情報を取得
        stats = inspector.get_statistics(filtered_logs)
        
        # レスポンス用にデータを整形
        logs_data = []
        for entry in filtered_logs:
            logs_data.append({
                'timestamp': entry['timestamp'],
                'level': entry['level'],
                'message': entry['message'],
                'raw_line': entry['raw_line']
            })
        
        return jsonify({
            "success": True,
            "logs": logs_data,
            "stats": stats,
            "total_count": len(filtered_logs)
        })
        
    except Exception as e:
        logger.exception(f"ログ検索中にエラーが発生: {str(e)}")
        return jsonify({"error": f"ログ検索中にエラーが発生しました: {str(e)}"}), 500

@log_viewer_bp.route('/structure/<structure_id>')
@login_required
def view_structure_logs(structure_id):
    """特定の構成IDのログを表示するページ"""
    try:
        # ログインスペクターを初期化
        inspector = LogInspector('app.log')
        
        # ログファイルを読み込み
        if not inspector.load_logs():
            return render_template('log_viewer/error.html', 
                                 error="ログファイルの読み込みに失敗しました")
        
        # 構成IDでフィルタリング
        filtered_logs = inspector.filter_by_structure_id(structure_id)
        
        # 統計情報を取得
        stats = inspector.get_statistics(filtered_logs)
        
        # ログデータを整形
        logs_data = []
        for entry in filtered_logs:
            logs_data.append({
                'timestamp': entry['timestamp'],
                'level': entry['level'],
                'message': entry['message'],
                'raw_line': entry['raw_line']
            })
        
        return render_template('log_viewer/structure_logs.html',
                             structure_id=structure_id,
                             logs=logs_data,
                             stats=stats)
        
    except Exception as e:
        logger.exception(f"構成ログ表示中にエラーが発生: {str(e)}")
        return render_template('log_viewer/error.html', 
                             error=f"エラーが発生しました: {str(e)}")

@log_viewer_bp.route('/user/<user_id>')
@login_required
def view_user_logs(user_id):
    """特定のユーザーIDのログを表示するページ"""
    try:
        # ログインスペクターを初期化
        inspector = LogInspector('app.log')
        
        # ログファイルを読み込み
        if not inspector.load_logs():
            return render_template('log_viewer/error.html', 
                                 error="ログファイルの読み込みに失敗しました")
        
        # ユーザーIDでフィルタリング
        filtered_logs = inspector.filter_by_user_id(user_id)
        
        # 統計情報を取得
        stats = inspector.get_statistics(filtered_logs)
        
        # ログデータを整形
        logs_data = []
        for entry in filtered_logs:
            logs_data.append({
                'timestamp': entry['timestamp'],
                'level': entry['level'],
                'message': entry['message'],
                'raw_line': entry['raw_line']
            })
        
        return render_template('log_viewer/user_logs.html',
                             user_id=user_id,
                             logs=logs_data,
                             stats=stats)
        
    except Exception as e:
        logger.exception(f"ユーザーログ表示中にエラーが発生: {str(e)}")
        return render_template('log_viewer/error.html', 
                             error=f"エラーが発生しました: {str(e)}")

@log_viewer_bp.route('/stats')
@login_required
def view_stats():
    """ログ統計情報を表示するページ"""
    try:
        # ログインスペクターを初期化
        inspector = LogInspector('app.log')
        
        # ログファイルを読み込み
        if not inspector.load_logs():
            return render_template('log_viewer/error.html', 
                                 error="ログファイルの読み込みに失敗しました")
        
        # 全体の統計情報を取得
        stats = inspector.get_statistics(inspector.log_entries)
        
        return render_template('log_viewer/stats.html', stats=stats)
        
    except Exception as e:
        logger.exception(f"統計情報表示中にエラーが発生: {str(e)}")
        return render_template('log_viewer/error.html', 
                             error=f"エラーが発生しました: {str(e)}")

@log_viewer_bp.route('/api/stats')
@login_required
def get_stats():
    """統計情報API"""
    try:
        # ログインスペクターを初期化
        inspector = LogInspector('app.log')
        
        # ログファイルを読み込み
        if not inspector.load_logs():
            return jsonify({"error": "ログファイルの読み込みに失敗しました"}), 500
        
        # 全体の統計情報を取得
        stats = inspector.get_statistics(inspector.log_entries)
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.exception(f"統計情報取得中にエラーが発生: {str(e)}")
        return jsonify({"error": f"統計情報取得中にエラーが発生しました: {str(e)}"}), 500 