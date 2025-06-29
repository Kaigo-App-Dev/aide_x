"""
ChatGPT出力のJSON抽出テスト
強化された厳密な構造（modules/type/id/fieldsなど）に対応
"""

import pytest
import json
from src.utils.files import extract_json_part
from src.routes.unified_routes import _validate_structure_completeness, _validate_module

class TestChatGPTExtraction:
    """ChatGPT出力のJSON抽出テストクラス"""
    
    def test_extract_valid_structure_json(self):
        """有効な構成JSONの抽出テスト"""
        valid_json = """
        {
          "title": "ブログサイト構成",
          "description": "個人ブログサイトの基本構成",
          "modules": [
            {
              "id": "header-001",
              "type": "component",
              "title": "ヘッダー",
              "description": "サイトのヘッダー部分",
              "component_config": {
                "logo": "サイトロゴ",
                "navigation": ["ホーム", "記事", "カテゴリ", "お問い合わせ"],
                "search": true
              }
            },
            {
              "id": "article-list-001",
              "type": "table",
              "title": "記事一覧",
              "description": "最新記事の表示",
              "columns": [
                {"key": "title", "label": "タイトル", "type": "text"},
                {"key": "author", "label": "著者", "type": "text"},
                {"key": "date", "label": "投稿日", "type": "date"},
                {"key": "category", "label": "カテゴリ", "type": "badge"},
                {"key": "actions", "label": "操作", "type": "actions"}
              ]
            }
          ]
        }
        """
        
        result = extract_json_part(valid_json)
        assert result is not None
        assert "error" not in result
        assert result["title"] == "ブログサイト構成"
        assert "modules" in result
        assert len(result["modules"]) == 2
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        assert len(validation["missing_fields"]) == 0
        assert len(validation["invalid_modules"]) == 0

    def test_extract_form_module_structure(self):
        """フォームモジュール構造の抽出テスト"""
        form_json = """
        {
          "title": "ユーザー管理システム",
          "description": "ユーザーの登録・編集・削除機能",
          "modules": [
            {
              "id": "user-form-001",
              "type": "form",
              "title": "ユーザー登録フォーム",
              "description": "新規ユーザーの登録フォーム",
              "fields": [
                {"label": "名前", "name": "name", "type": "text", "required": true},
                {"label": "メールアドレス", "name": "email", "type": "email", "required": true},
                {"label": "パスワード", "name": "password", "type": "password", "required": true},
                {"label": "生年月日", "name": "birthdate", "type": "date", "required": false},
                {"label": "性別", "name": "gender", "type": "select", "options": ["男性", "女性", "その他"], "required": false},
                {"label": "利用規約同意", "name": "terms", "type": "checkbox", "required": true}
              ]
            }
          ]
        }
        """
        
        result = extract_json_part(form_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "form"
        assert "fields" in module
        assert len(module["fields"]) == 6

    def test_extract_table_module_structure(self):
        """テーブルモジュール構造の抽出テスト"""
        table_json = """
        {
          "title": "商品管理システム",
          "description": "商品の一覧・詳細・編集機能",
          "modules": [
            {
              "id": "product-table-001",
              "type": "table",
              "title": "商品一覧",
              "description": "商品の一覧表示と操作",
              "columns": [
                {"key": "id", "label": "商品ID", "type": "text"},
                {"key": "name", "label": "商品名", "type": "text"},
                {"key": "price", "label": "価格", "type": "number"},
                {"key": "category", "label": "カテゴリ", "type": "badge"},
                {"key": "status", "label": "ステータス", "type": "status"},
                {"key": "created_at", "label": "登録日", "type": "date"},
                {"key": "actions", "label": "操作", "type": "actions"}
              ]
            }
          ]
        }
        """
        
        result = extract_json_part(table_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "table"
        assert "columns" in module
        assert len(module["columns"]) == 7

    def test_extract_api_module_structure(self):
        """APIモジュール構造の抽出テスト"""
        api_json = """
        {
          "title": "REST API設計",
          "description": "Webアプリケーション用のREST API設計",
          "modules": [
            {
              "id": "user-api-001",
              "type": "api",
              "title": "ユーザーAPI",
              "description": "ユーザー管理用のREST API",
              "endpoints": [
                {
                  "method": "GET",
                  "path": "/api/users",
                  "description": "ユーザー一覧取得",
                  "parameters": [
                    {"name": "page", "type": "integer", "required": false},
                    {"name": "limit", "type": "integer", "required": false}
                  ]
                },
                {
                  "method": "POST",
                  "path": "/api/users",
                  "description": "ユーザー作成",
                  "parameters": [
                    {"name": "name", "type": "string", "required": true},
                    {"name": "email", "type": "string", "required": true}
                  ]
                },
                {
                  "method": "GET",
                  "path": "/api/users/{id}",
                  "description": "ユーザー詳細取得",
                  "parameters": [
                    {"name": "id", "type": "integer", "required": true}
                  ]
                }
              ]
            }
          ]
        }
        """
        
        result = extract_json_part(api_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "api"
        assert "endpoints" in module
        assert len(module["endpoints"]) == 3

    def test_extract_chart_module_structure(self):
        """チャートモジュール構造の抽出テスト"""
        chart_json = """
        {
          "title": "データ分析ダッシュボード",
          "description": "売上・ユーザー・商品の分析ダッシュボード",
          "modules": [
            {
              "id": "sales-chart-001",
              "type": "chart",
              "title": "売上分析チャート",
              "description": "月別売上推移のグラフ表示",
              "chart_config": {
                "chart_type": "line",
                "data_source": "sales_data",
                "x_axis": "month",
                "y_axis": "sales_amount",
                "options": {
                  "responsive": true,
                  "scales": {
                    "y": {"beginAtZero": true}
                  }
                }
              }
            }
          ]
        }
        """
        
        result = extract_json_part(chart_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "chart"
        assert "chart_config" in module

    def test_extract_auth_module_structure(self):
        """認証モジュール構造の抽出テスト"""
        auth_json = """
        {
          "title": "認証システム",
          "description": "ユーザー認証・認可機能",
          "modules": [
            {
              "id": "auth-system-001",
              "type": "auth",
              "title": "認証システム",
              "description": "ログイン・ログアウト・パスワードリセット機能",
              "auth_config": {
                "login_methods": ["email_password", "oauth_google", "oauth_github"],
                "password_policy": {
                  "min_length": 8,
                  "require_uppercase": true,
                  "require_lowercase": true,
                  "require_numbers": true,
                  "require_special_chars": true
                },
                "session_timeout": 3600,
                "max_login_attempts": 5,
                "lockout_duration": 1800
              }
            }
          ]
        }
        """
        
        result = extract_json_part(auth_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "auth"
        assert "auth_config" in module

    def test_extract_database_module_structure(self):
        """データベースモジュール構造の抽出テスト"""
        database_json = """
        {
          "title": "データベース設計",
          "description": "アプリケーション用のデータベース設計",
          "modules": [
            {
              "id": "user-db-001",
              "type": "database",
              "title": "ユーザーテーブル設計",
              "description": "ユーザー情報を格納するテーブル設計",
              "tables": [
                {
                  "name": "users",
                  "description": "ユーザー基本情報テーブル",
                  "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": true, "auto_increment": true},
                    {"name": "name", "type": "VARCHAR(255)", "not_null": true},
                    {"name": "email", "type": "VARCHAR(255)", "not_null": true, "unique": true},
                    {"name": "password_hash", "type": "VARCHAR(255)", "not_null": true},
                    {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
                    {"name": "updated_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"}
                  ]
                }
              ]
            }
          ]
        }
        """
        
        result = extract_json_part(database_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "database"
        assert "tables" in module

    def test_extract_config_module_structure(self):
        """設定モジュール構造の抽出テスト"""
        config_json = """
        {
          "title": "システム設定",
          "description": "アプリケーションの設定管理",
          "modules": [
            {
              "id": "app-config-001",
              "type": "config",
              "title": "アプリケーション設定",
              "description": "アプリケーション全体の設定項目",
              "settings": [
                {
                  "key": "app_name",
                  "label": "アプリケーション名",
                  "type": "text",
                  "default": "MyApp",
                  "description": "アプリケーションの表示名"
                },
                {
                  "key": "debug_mode",
                  "label": "デバッグモード",
                  "type": "boolean",
                  "default": false,
                  "description": "デバッグ情報の表示"
                },
                {
                  "key": "timezone",
                  "label": "タイムゾーン",
                  "type": "select",
                  "options": ["UTC", "Asia/Tokyo", "America/New_York"],
                  "default": "UTC",
                  "description": "システムのタイムゾーン"
                }
              ]
            }
          ]
        }
        """
        
        result = extract_json_part(config_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "config"
        assert "settings" in module

    def test_extract_page_module_structure(self):
        """ページモジュール構造の抽出テスト"""
        page_json = """
        {
          "title": "ページレイアウト設計",
          "description": "Webページのレイアウト設計",
          "modules": [
            {
              "id": "main-page-001",
              "type": "page",
              "title": "メインページ",
              "description": "アプリケーションのメインページレイアウト",
              "layout": {
                "header": {
                  "height": "60px",
                  "components": ["logo", "navigation", "search", "user_menu"]
                },
                "sidebar": {
                  "width": "250px",
                  "position": "left",
                  "components": ["menu", "filters", "quick_actions"]
                },
                "main_content": {
                  "components": ["breadcrumb", "content_area", "pagination"]
                },
                "footer": {
                  "height": "40px",
                  "components": ["copyright", "links", "social_media"]
                }
              }
            }
          ]
        }
        """
        
        result = extract_json_part(page_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "page"
        assert "layout" in module

    def test_extract_component_module_structure(self):
        """コンポーネントモジュール構造の抽出テスト"""
        component_json = """
        {
          "title": "UIコンポーネント設計",
          "description": "再利用可能なUIコンポーネントの設計",
          "modules": [
            {
              "id": "header-component-001",
              "type": "component",
              "title": "ヘッダーコンポーネント",
              "description": "サイト全体で使用するヘッダーコンポーネント",
              "component_config": {
                "props": [
                  {"name": "title", "type": "string", "required": true},
                  {"name": "show_search", "type": "boolean", "default": true},
                  {"name": "show_user_menu", "type": "boolean", "default": true}
                ],
                "events": ["search", "logout", "profile_click"],
                "styles": {
                  "height": "60px",
                  "background": "#ffffff",
                  "border_bottom": "1px solid #e1e5e9"
                }
              }
            }
          ]
        }
        """
        
        result = extract_json_part(component_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # モジュール検証
        module = result["modules"][0]
        module_validation = _validate_module(module, 0)
        assert module_validation["is_valid"] is True
        assert module["type"] == "component"
        assert "component_config" in module

    def test_extract_mixed_module_structure(self):
        """複数モジュールタイプの混合構造テスト"""
        mixed_json = """
        {
          "title": "ECサイト管理システム",
          "description": "商品管理・注文管理・ユーザー管理の統合システム",
          "modules": [
            {
              "id": "product-form-001",
              "type": "form",
              "title": "商品登録フォーム",
              "description": "新規商品の登録フォーム",
              "fields": [
                {"label": "商品名", "name": "name", "type": "text", "required": true},
                {"label": "価格", "name": "price", "type": "number", "required": true},
                {"label": "カテゴリ", "name": "category", "type": "select", "options": ["食品", "衣類", "電子機器"], "required": true},
                {"label": "説明", "name": "description", "type": "textarea", "required": false}
              ]
            },
            {
              "id": "order-table-001",
              "type": "table",
              "title": "注文一覧",
              "description": "注文情報の一覧表示",
              "columns": [
                {"key": "order_id", "label": "注文ID", "type": "text"},
                {"key": "customer_name", "label": "顧客名", "type": "text"},
                {"key": "total_amount", "label": "合計金額", "type": "number"},
                {"key": "status", "label": "ステータス", "type": "badge"},
                {"key": "order_date", "label": "注文日", "type": "date"},
                {"key": "actions", "label": "操作", "type": "actions"}
              ]
            },
            {
              "id": "sales-chart-001",
              "type": "chart",
              "title": "売上分析",
              "description": "日別・月別売上のグラフ表示",
              "chart_config": {
                "chart_type": "bar",
                "data_source": "sales_data",
                "x_axis": "date",
                "y_axis": "sales_amount"
              }
            }
          ]
        }
        """
        
        result = extract_json_part(mixed_json)
        assert result is not None
        assert "error" not in result
        
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        assert len(validation["invalid_modules"]) == 0
        
        # 各モジュールの検証
        modules = result["modules"]
        assert len(modules) == 3
        
        # フォームモジュール
        form_module = modules[0]
        assert form_module["type"] == "form"
        assert "fields" in form_module
        assert len(form_module["fields"]) == 4
        
        # テーブルモジュール
        table_module = modules[1]
        assert table_module["type"] == "table"
        assert "columns" in table_module
        assert len(table_module["columns"]) == 6
        
        # チャートモジュール
        chart_module = modules[2]
        assert chart_module["type"] == "chart"
        assert "chart_config" in chart_module

    def test_validate_invalid_structure(self):
        """無効な構造の検証テスト"""
        invalid_json = {
            "title": "不完全な構成",
            # modulesが欠落
        }
        
        validation = _validate_structure_completeness(invalid_json)
        assert validation["is_valid"] is False
        assert "modules" in validation["missing_fields"]

    def test_validate_invalid_module(self):
        """無効なモジュールの検証テスト"""
        invalid_module = {
            "id": "invalid-module",
            # typeとtitleが欠落
        }
        
        validation = _validate_module(invalid_module, 0)
        assert validation["is_valid"] is False
        assert len(validation["errors"]) > 0

    def test_validate_form_module_without_fields(self):
        """fieldsが欠落したフォームモジュールの検証テスト"""
        invalid_form_module = {
            "id": "form-001",
            "type": "form",
            "title": "不完全なフォーム",
            # fieldsが欠落
        }
        
        validation = _validate_module(invalid_form_module, 0)
        assert validation["is_valid"] is False
        assert any("fields" in error for error in validation["errors"])

    def test_validate_table_module_without_columns(self):
        """columnsが欠落したテーブルモジュールの検証テスト"""
        invalid_table_module = {
            "id": "table-001",
            "type": "table",
            "title": "不完全なテーブル",
            # columnsが欠落
        }
        
        validation = _validate_module(invalid_table_module, 0)
        assert validation["is_valid"] is False
        assert any("columns" in error for error in validation["errors"])

    def test_extract_json_with_code_block(self):
        """コードブロックで囲まれたJSONの抽出テスト"""
        json_with_code_block = """
        以下はブログサイトの構成です：

        ```json
        {
          "title": "ブログサイト構成",
          "description": "個人ブログサイトの基本構成",
          "modules": [
            {
              "id": "header-001",
              "type": "component",
              "title": "ヘッダー",
              "description": "サイトのヘッダー部分",
              "component_config": {
                "logo": "サイトロゴ",
                "navigation": ["ホーム", "記事", "カテゴリ"]
              }
            }
          ]
        }
        ```

        この構成でよろしいでしょうか？
        """
        
        result = extract_json_part(json_with_code_block)
        assert result is not None
        assert "error" not in result
        assert result["title"] == "ブログサイト構成"
        assert "modules" in result
        assert len(result["modules"]) == 1

    def test_extract_json_with_extra_text(self):
        """余分なテキストを含むJSONの抽出テスト"""
        json_with_extra_text = """
        ユーザーの要求に基づいて、以下の構成を作成しました：

        {
          "title": "ECサイト構成",
          "description": "オンラインショップの基本構成",
          "modules": [
            {
              "id": "product-catalog-001",
              "type": "table",
              "title": "商品カタログ",
              "description": "商品の一覧表示",
              "columns": [
                {"key": "id", "label": "商品ID", "type": "text"},
                {"key": "name", "label": "商品名", "type": "text"},
                {"key": "price", "label": "価格", "type": "number"}
              ]
            }
          ]
        }

        この構成は現代的なECサイトに必要な機能を含んでいます。
        """
        
        result = extract_json_part(json_with_extra_text)
        assert result is not None
        assert "error" not in result
        assert result["title"] == "ECサイト構成"
        assert "modules" in result
        assert len(result["modules"]) == 1

    def test_target_structure_id_c9992ab0_2a55_4918_8609_11d076c7c547(self):
        """テスト対象構成ID c9992ab0-2a55-4918-8609-11d076c7c547 の完全な構成例"""
        target_structure_dict = {
            "title": "プロジェクト管理システム",
            "description": "タスク管理・チーム協働・進捗追跡の統合システム",
            "modules": [
                {
                    "id": "task-management-001",
                    "type": "table",
                    "title": "タスク管理",
                    "description": "プロジェクトタスクの一覧・作成・編集・削除",
                    "columns": [
                        {"key": "id", "label": "タスクID", "type": "text"},
                        {"key": "title", "label": "タスク名", "type": "text"},
                        {"key": "assignee", "label": "担当者", "type": "user"},
                        {"key": "priority", "label": "優先度", "type": "badge"},
                        {"key": "status", "label": "ステータス", "type": "status"},
                        {"key": "due_date", "label": "期限", "type": "date"},
                        {"key": "actions", "label": "操作", "type": "actions"}
                    ]
                },
                {
                    "id": "task-form-001",
                    "type": "form",
                    "title": "タスク作成・編集フォーム",
                    "description": "新しいタスクの作成と既存タスクの編集",
                    "fields": [
                        {"label": "タスク名", "name": "title", "type": "text", "required": True},
                        {"label": "説明", "name": "description", "type": "textarea", "required": False},
                        {"label": "担当者", "name": "assignee", "type": "select", "required": True, "options": ["選択してください"]},
                        {"label": "優先度", "name": "priority", "type": "select", "required": True, "options": ["低", "中", "高", "緊急"]},
                        {"label": "ステータス", "name": "status", "type": "select", "required": True, "options": ["未着手", "進行中", "レビュー中", "完了"]},
                        {"label": "期限", "name": "due_date", "type": "datetime", "required": False}
                    ]
                },
                {
                    "id": "progress-chart-001",
                    "type": "chart",
                    "title": "進捗分析",
                    "description": "プロジェクト全体の進捗を可視化",
                    "chart_config": {
                        "chart_type": "doughnut",
                        "data_source": "task_progress",
                        "title": "タスク進捗状況",
                        "options": {
                            "responsive": True,
                            "plugins": {
                                "legend": {"position": "bottom"},
                                "tooltip": {"enabled": True}
                            }
                        }
                    }
                },
                {
                    "id": "project-api-001",
                    "type": "api",
                    "title": "プロジェクトAPI",
                    "description": "プロジェクト管理用のREST API",
                    "endpoints": [
                        {
                            "method": "GET",
                            "path": "/api/projects",
                            "description": "プロジェクト一覧取得",
                            "parameters": [
                                {"name": "page", "type": "integer", "required": False, "default": 1},
                                {"name": "limit", "type": "integer", "required": False, "default": 20}
                            ]
                        },
                        {
                            "method": "POST",
                            "path": "/api/projects",
                            "description": "プロジェクト作成",
                            "parameters": [
                                {"name": "name", "type": "string", "required": True},
                                {"name": "description", "type": "string", "required": False}
                            ]
                        }
                    ]
                },
                {
                    "id": "user-auth-001",
                    "type": "auth",
                    "title": "ユーザー認証",
                    "description": "ログイン・ログアウト・パスワード管理",
                    "auth_config": {
                        "login_methods": ["email_password", "oauth_google", "oauth_github"],
                        "password_policy": {
                            "min_length": 8,
                            "require_uppercase": True,
                            "require_lowercase": True,
                            "require_numbers": True,
                            "require_special_chars": True
                        },
                        "session_config": {
                            "timeout_minutes": 480,
                            "remember_me_days": 30,
                            "max_concurrent_sessions": 3
                        }
                    }
                }
            ]
        }
        target_structure_json = json.dumps(target_structure_dict, ensure_ascii=False)
        result = extract_json_part(target_structure_json)
        assert result is not None
        assert "error" not in result
        assert result["title"] == "プロジェクト管理システム"
        assert "modules" in result
        assert len(result["modules"]) == 5
        # 構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        assert len(validation["missing_fields"]) == 0
        assert len(validation["invalid_modules"]) == 0
        # 各モジュールタイプの検証
        modules = result["modules"]
        table_module = next(m for m in modules if m["type"] == "table")
        assert table_module["id"] == "task-management-001"
        assert "columns" in table_module
        assert len(table_module["columns"]) == 7
        form_module = next(m for m in modules if m["type"] == "form")
        assert form_module["id"] == "task-form-001"
        assert "fields" in form_module
        assert len(form_module["fields"]) == 6
        chart_module = next(m for m in modules if m["type"] == "chart")
        assert chart_module["id"] == "progress-chart-001"
        assert "chart_config" in chart_module
        api_module = next(m for m in modules if m["type"] == "api")
        assert api_module["id"] == "project-api-001"
        assert "endpoints" in api_module
        assert len(api_module["endpoints"]) == 2
        auth_module = next(m for m in modules if m["type"] == "auth")
        assert auth_module["id"] == "user-auth-001"
        assert "auth_config" in auth_module

    def test_claude_evaluation_compatibility(self):
        """Claude評価との互換性テスト"""
        claude_friendly_json = """
        {
          "title": "シンプルなブログシステム",
          "description": "個人ブログに必要な最小限の機能",
          "modules": [
            {
              "id": "blog-post-001",
              "type": "form",
              "title": "記事投稿フォーム",
              "description": "新しいブログ記事を作成するフォーム",
              "fields": [
                {"label": "タイトル", "name": "title", "type": "text", "required": true},
                {"label": "本文", "name": "content", "type": "textarea", "required": true},
                {"label": "カテゴリ", "name": "category", "type": "select", "options": ["技術", "生活", "趣味"], "required": false}
              ]
            },
            {
              "id": "blog-list-001",
              "type": "table",
              "title": "記事一覧",
              "description": "投稿済み記事の一覧表示",
              "columns": [
                {"key": "title", "label": "タイトル", "type": "text"},
                {"key": "author", "label": "著者", "type": "text"},
                {"key": "category", "label": "カテゴリ", "type": "badge"},
                {"key": "published_at", "label": "投稿日", "type": "date"},
                {"key": "actions", "label": "操作", "type": "actions"}
              ]
            }
          ]
        }
        """
        
        result = extract_json_part(claude_friendly_json)
        assert result is not None
        assert "error" not in result
        
        # Claude評価用の構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # Claudeが評価しやすい構造であることを確認
        assert result["title"] is not None and len(result["title"]) > 0
        assert result["description"] is not None
        assert len(result["modules"]) > 0
        
        for module in result["modules"]:
            assert module["title"] is not None and len(module["title"]) > 0
            assert module["description"] is not None
            assert module["type"] in ["form", "table", "api", "chart", "auth", "database", "config", "page", "component"]

    def test_gemini_rendering_compatibility(self):
        """Gemini描画との互換性テスト"""
        gemini_friendly_json = """
        {
          "title": "ダッシュボードシステム",
          "description": "データ可視化と管理機能",
          "modules": [
            {
              "id": "user-input-001",
              "type": "form",
              "title": "データ入力フォーム",
              "description": "分析用データの入力",
              "fields": [
                {"label": "データ名", "name": "data_name", "type": "text", "required": true},
                {"label": "数値", "name": "value", "type": "number", "required": true},
                {"label": "日付", "name": "date", "type": "date", "required": true},
                {"label": "カテゴリ", "name": "category", "type": "select", "options": ["売上", "ユーザー", "商品"], "required": true}
              ]
            },
            {
              "id": "data-display-001",
              "type": "table",
              "title": "データ一覧",
              "description": "入力されたデータの一覧表示",
              "columns": [
                {"key": "data_name", "label": "データ名", "type": "text"},
                {"key": "value", "label": "数値", "type": "number"},
                {"key": "date", "label": "日付", "type": "date"},
                {"key": "category", "label": "カテゴリ", "type": "badge"},
                {"key": "actions", "label": "操作", "type": "actions"}
              ]
            },
            {
              "id": "visualization-001",
              "type": "chart",
              "title": "データ可視化",
              "description": "データのグラフ表示",
              "chart_config": {
                "chart_type": "line",
                "data_source": "input_data",
                "x_axis": "date",
                "y_axis": "value",
                "title": "データ推移",
                "options": {
                  "responsive": true,
                  "scales": {
                    "y": {"beginAtZero": true}
                  }
                }
              }
            }
          ]
        }
        """
        
        result = extract_json_part(gemini_friendly_json)
        assert result is not None
        assert "error" not in result
        
        # Gemini描画用の構造検証
        validation = _validate_structure_completeness(result)
        assert validation["is_valid"] is True
        
        # Geminiが描画しやすい構造であることを確認
        modules = result["modules"]
        
        # フォームモジュールの検証
        form_module = next(m for m in modules if m["type"] == "form")
        assert "fields" in form_module
        for field in form_module["fields"]:
            assert "label" in field
            assert "name" in field
            assert "type" in field
        
        # テーブルモジュールの検証
        table_module = next(m for m in modules if m["type"] == "table")
        assert "columns" in table_module
        for column in table_module["columns"]:
            assert "key" in column
            assert "label" in column
            assert "type" in column
        
        # チャートモジュールの検証
        chart_module = next(m for m in modules if m["type"] == "chart")
        assert "chart_config" in chart_module
        chart_config = chart_module["chart_config"]
        assert "chart_type" in chart_config
        assert "data_source" in chart_config 