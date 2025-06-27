#!/usr/bin/env python3
"""
テンプレート読み込み問題のデバッグスクリプト
"""

import os
import sys
from pathlib import Path

def check_template_paths():
    """テンプレートパスの確認"""
    print("=== テンプレートパス確認 ===")
    
    # 現在のディレクトリ
    current_dir = os.getcwd()
    print(f"現在のディレクトリ: {current_dir}")
    
    # プロジェクトルートの推定
    project_root = current_dir
    if not os.path.exists(os.path.join(project_root, 'templates')):
        # srcディレクトリの親を試す
        src_parent = os.path.dirname(os.path.join(current_dir, 'src'))
        if os.path.exists(os.path.join(src_parent, 'templates')):
            project_root = src_parent
            print(f"プロジェクトルートを検出: {project_root}")
    
    # テンプレートフォルダの確認
    template_folder = os.path.join(project_root, 'templates')
    print(f"テンプレートフォルダ: {template_folder}")
    print(f"テンプレートフォルダ存在: {os.path.exists(template_folder)}")
    
    if os.path.exists(template_folder):
        # テンプレートファイルの確認
        error_500_path = os.path.join(template_folder, 'errors', '500.html')
        print(f"500.htmlパス: {error_500_path}")
        print(f"500.html存在: {os.path.exists(error_500_path)}")
        
        if os.path.exists(error_500_path):
            # ファイルサイズの確認
            file_size = os.path.getsize(error_500_path)
            print(f"500.htmlサイズ: {file_size} bytes")
            
            # ファイル内容の確認（最初の100文字）
            try:
                with open(error_500_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                    print(f"500.html内容（最初の100文字）: {repr(content)}")
            except Exception as e:
                print(f"500.html読み込みエラー: {e}")
    
    return template_folder

def test_flask_template_loading():
    """Flaskテンプレート読み込みのテスト"""
    print("\n=== Flaskテンプレート読み込みテスト ===")
    
    try:
        from flask import Flask
        import os
        
        # プロジェクトルートの取得
        project_root = os.getcwd()
        if not os.path.exists(os.path.join(project_root, 'templates')):
            project_root = os.path.dirname(os.path.join(project_root, 'src'))
        
        template_folder = os.path.join(project_root, 'templates')
        static_folder = os.path.join(project_root, 'static')
        
        print(f"Flask初期化パラメータ:")
        print(f"  template_folder: {template_folder}")
        print(f"  static_folder: {static_folder}")
        
        # Flaskアプリの作成
        app = Flask(__name__, 
                    template_folder=template_folder,
                    static_folder=static_folder)
        
        # テンプレートフォルダの確認
        print(f"Flask template_folder: {app.template_folder}")
        print(f"Flask template_folder存在: {os.path.exists(app.template_folder)}")
        
        # テンプレートの存在確認
        from flask import render_template_string
        try:
            # シンプルなテンプレートのテスト
            result = render_template_string("Hello {{ name }}!", name="World")
            print(f"テンプレート文字列テスト: {result}")
        except Exception as e:
            print(f"テンプレート文字列テストエラー: {e}")
        
        # ファイルテンプレートのテスト
        try:
            from flask import render_template
            # 500.htmlの存在確認
            error_template_path = os.path.join(app.template_folder, 'errors', '500.html')
            if os.path.exists(error_template_path):
                print(f"500.htmlテンプレート存在確認: OK")
                
                # 実際のレンダリングテスト
                try:
                    result = render_template('errors/500.html', error="テストエラー")
                    print(f"500.htmlレンダリングテスト: 成功（{len(result)}文字）")
                except Exception as e:
                    print(f"500.htmlレンダリングテストエラー: {e}")
            else:
                print(f"500.htmlテンプレート存在確認: NG - {error_template_path}")
        except Exception as e:
            print(f"ファイルテンプレートテストエラー: {e}")
        
    except Exception as e:
        print(f"Flaskテストエラー: {e}")

def test_unified_interface_template():
    """統合インターフェーステンプレートのテスト"""
    print("\n=== 統合インターフェーステンプレートテスト ===")
    
    try:
        from flask import Flask
        import os
        
        # プロジェクトルートの取得
        project_root = os.getcwd()
        if not os.path.exists(os.path.join(project_root, 'templates')):
            project_root = os.path.dirname(os.path.join(project_root, 'src'))
        
        template_folder = os.path.join(project_root, 'templates')
        
        # Flaskアプリの作成
        app = Flask(__name__, template_folder=template_folder)
        
        # unified_interface.htmlの存在確認
        unified_template_path = os.path.join(app.template_folder, 'structure', 'unified_interface.html')
        print(f"unified_interface.htmlパス: {unified_template_path}")
        print(f"unified_interface.html存在: {os.path.exists(unified_template_path)}")
        
        if os.path.exists(unified_template_path):
            # ファイルサイズの確認
            file_size = os.path.getsize(unified_template_path)
            print(f"unified_interface.htmlサイズ: {file_size} bytes")
            
            # ファイル内容の確認（最初の100文字）
            try:
                with open(unified_template_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                    print(f"unified_interface.html内容（最初の100文字）: {repr(content)}")
            except Exception as e:
                print(f"unified_interface.html読み込みエラー: {e}")
        
    except Exception as e:
        print(f"統合インターフェーステンプレートテストエラー: {e}")

def test_app_creation():
    """アプリケーション作成のテスト"""
    print("\n=== アプリケーション作成テスト ===")
    
    try:
        # srcディレクトリをパスに追加
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # アプリケーションの作成
        from app import create_app
        
        print("アプリケーション作成開始...")
        app = create_app()
        print("アプリケーション作成成功")
        
        # テンプレートフォルダの確認
        print(f"アプリ template_folder: {app.template_folder}")
        print(f"アプリ template_folder存在: {os.path.exists(app.template_folder)}")
        
        # 静的ファイルフォルダの確認
        print(f"アプリ static_folder: {app.static_folder}")
        print(f"アプリ static_folder存在: {os.path.exists(app.static_folder)}")
        
        return app
        
    except Exception as e:
        print(f"アプリケーション作成テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン関数"""
    print("🧪 テンプレート読み込み問題デバッグスクリプト")
    print("=" * 50)
    
    # 1. テンプレートパスの確認
    template_folder = check_template_paths()
    
    # 2. Flaskテンプレート読み込みのテスト
    test_flask_template_loading()
    
    # 3. 統合インターフェーステンプレートのテスト
    test_unified_interface_template()
    
    # 4. アプリケーション作成のテスト
    app = test_app_creation()
    
    print("\n" + "=" * 50)
    print("✅ デバッグ完了")
    
    if app:
        print("🎉 アプリケーション作成に成功しました")
    else:
        print("❌ アプリケーション作成に失敗しました")

if __name__ == "__main__":
    main() 