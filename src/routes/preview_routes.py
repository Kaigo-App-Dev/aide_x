"""
プレビュールート定義モジュール
"""

from flask import Blueprint, request, jsonify, render_template_string
from src.llm.controller import AIController
from src.structure.utils import load_structure_by_id, is_ui_ready
import json
import logging

logger = logging.getLogger(__name__)

preview_bp = Blueprint('preview', __name__, url_prefix='/preview')

@preview_bp.route('/new', methods=['POST'])
def new_preview():
    """新しいプレビューの作成"""
    try:
        data = request.get_json()
        if not data or 'user_input' not in data:
            return jsonify({
                'error': 'Invalid request data',
                'message': 'user_input is required'
            }), 400
        
        # TODO: AIコントローラーを使用してプレビューを生成
        return jsonify({
            'status': 'ok',
            'message': 'Preview created successfully'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to create preview'
        }), 500

@preview_bp.route('/<structure_id>')
def preview_structure(structure_id):
    """
    構成をHTMLプレビューとして表示する
    
    Args:
        structure_id: 構成のID
        
    Returns:
        str: レンダリングされたHTML
    """
    try:
        logger.info(f"🎨 プレビュー生成開始 - structure_id: {structure_id}")
        
        # 構成データを読み込み
        structure = load_structure_by_id(structure_id)
        if not structure:
            logger.warning(f"❌ 構成が見つかりません - structure_id: {structure_id}")
            return f"<div style='padding: 20px; color: #ff6b6b;'>構成が見つかりません: {structure_id}</div>", 404
        
        content = structure.get("content", {})
        
        # UI準備状態をチェック
        ui_ready = is_ui_ready(structure)
        if not ui_ready:
            logger.info(f"ℹ️ UI準備未完了 - structure_id: {structure_id}")
            return render_template_string("""
                <div style="padding: 20px; text-align: center; color: #858585;">
                    <h3>🎨 UIプレビュー</h3>
                    <p>この構成はまだUI出力に適していません。</p>
                    <p style="font-size: 12px; margin-top: 10px;">
                        チャットでUI構成について詳しく説明してください。
                    </p>
                </div>
            """)
        
        # HTMLが直接含まれている場合
        if isinstance(content, str) and ("<div" in content or "<html" in content):
            logger.info(f"✅ HTML直接表示 - structure_id: {structure_id}")
            return content
        
        # 構造化データの場合、HTMLテンプレートを生成
        logger.info(f"✅ 構造化データからHTML生成 - structure_id: {structure_id}")
        return render_structure_to_html(content)
        
    except Exception as e:
        logger.error(f"❌ プレビュー生成エラー - structure_id: {structure_id}, error: {str(e)}")
        return f"<div style='padding: 20px; color: #ff6b6b;'>プレビュー生成エラー: {str(e)}</div>", 500

def render_structure_to_html(content) -> str:
    """
    構造化データをHTMLにレンダリングする
    
    Args:
        content: 構造化データまたは文字列
        
    Returns:
        str: レンダリングされたHTML
    """
    try:
        # contentが文字列の場合はそのまま返す
        if isinstance(content, str):
            return content
        
        # contentが辞書でない場合はエラー
        if not isinstance(content, dict):
            return f"<div style='padding: 20px; color: #ff6b6b;'>サポートされていないデータ形式: {type(content)}</div>"
        
        title = content.get("title", "無題のプロジェクト")
        description = content.get("description", "説明がありません")
        
        # 基本HTMLテンプレート
        html_template = """
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ title }}</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                    color: #333;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 300;
                }
                .header p {
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 1.1em;
                }
                .content {
                    padding: 30px;
                }
                .section {
                    margin-bottom: 30px;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    background: #fafafa;
                }
                .section h3 {
                    margin: 0 0 15px 0;
                    color: #333;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 8px;
                }
                .component {
                    background: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 4px;
                    border-left: 4px solid #667eea;
                }
                .component h4 {
                    margin: 0 0 8px 0;
                    color: #667eea;
                }
                .component p {
                    margin: 0;
                    color: #666;
                    font-size: 14px;
                }
                .tech-stack {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 10px;
                }
                .tech-tag {
                    background: #667eea;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 500;
                }
                .status {
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 500;
                    margin-left: 10px;
                }
                .status.ready {
                    background: #4caf50;
                    color: white;
                }
                .status.pending {
                    background: #ff9800;
                    color: white;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ title }}</h1>
                    <p>{{ description }}</p>
                </div>
                <div class="content">
                    {% for section_name, section_data in content.items() %}
                    <div class="section">
                        <h3>{{ section_name }}</h3>
                        {% if section_data is mapping %}
                            {% for key, value in section_data.items() %}
                            <div class="component">
                                <h4>{{ key }}</h4>
                                {% if value is mapping %}
                                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 12px; overflow-x: auto;">{{ value | tojson(indent=2) }}</pre>
                                {% elif value is string %}
                                    <p>{{ value }}</p>
                                {% else %}
                                    <p>{{ value | string }}</p>
                                {% endif %}
                            </div>
                            {% endfor %}
                        {% elif section_data is string %}
                            <p>{{ section_data }}</p>
                        {% else %}
                            <p>{{ section_data | string }}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(html_template, 
                                    title=title, 
                                    description=description, 
                                    content=content.get("content", {}))
        
    except Exception as e:
        logger.error(f"❌ HTMLレンダリングエラー: {str(e)}")
        return f"""
        <div style="padding: 20px; color: #ff6b6b;">
            <h3>レンダリングエラー</h3>
            <p>HTMLの生成中にエラーが発生しました: {str(e)}</p>
        </div>
        """ 