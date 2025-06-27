"""
統合インターフェース用ルート

このモジュールは、構成編集、AI評価、履歴表示を1つの画面で統合するためのルートを提供します。
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import logging
from src.structure.utils import load_structure_by_id
from src.structure.history_manager import load_structure_history, get_history_summary

logger = logging.getLogger(__name__)

# Blueprintはinitからインポート
from . import structure_bp

@structure_bp.route("/unified/<structure_id>")
def unified_interface(structure_id):
    """
    統合インターフェースを表示する
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        str: 統合インターフェースのHTML
    """
    try:
        # 構造データを読み込み
        structure = load_structure_by_id(structure_id)
        if not structure:
            return render_template("errors/404.html"), 404
            
        return render_template(
            "structure/unified_interface.html",
            structure_id=structure_id,
            structure=structure,
            messages=[]  # チャットメッセージ用の空リスト
        )
    except Exception as e:
        logger.error(f"統合インターフェース表示中にエラーが発生: {str(e)}")
        return render_template("errors/500.html"), 500

@structure_bp.route("/unified/<structure_id>/status")
def unified_status(structure_id):
    """
    統合インターフェースの状態を取得するAPI
    
    Args:
        structure_id (str): 構造ID
        
    Returns:
        dict: 構造と履歴の状態情報
    """
    try:
        # 構造データを読み込み
        structure = load_structure_by_id(structure_id)
        if not structure:
            return jsonify({
                "success": False,
                "error": "構造が見つかりません",
                "structure_id": structure_id
            }), 404
        
        # 履歴サマリーを取得
        history_summary = get_history_summary(structure_id)
        
        # 履歴データを取得
        history_data = load_structure_history(structure_id)
        
        return jsonify({
            "success": True,
            "structure": {
                "id": structure.get("id"),
                "title": structure.get("title"),
                "description": structure.get("description"),
                "updated_at": structure.get("updated_at")
            },
            "history_summary": history_summary,
            "history_count": len(history_data["history"]) if history_data else 0
        })
        
    except Exception as e:
        logger.error(f"統合インターフェース状態取得中にエラーが発生: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"状態の取得中にエラーが発生しました: {str(e)}",
            "structure_id": structure_id
        }), 500

@structure_bp.route("/unified/minimal-test")
def minimal_test():
    """
    最小限のテスト用ルート
    """
    return render_template(
        "structure/unified_interface.html",
        structure_id="minimal-test",
        structure={"id": "minimal-test", "title": "テスト用構造"},
        messages=[]
    ) 