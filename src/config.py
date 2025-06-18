"""
アプリケーション設定

このモジュールは、アプリケーション全体で使用される設定を提供します。
"""

class Config:
    """アプリケーション設定クラス"""
    
    # デバッグモード
    DEBUG = True
    
    # ログレベル
    LOG_LEVEL = "INFO"
    
    # セキュリティ設定
    SECRET_KEY = "dev"  # 本番環境では必ず変更すること
    
    # CORS設定
    CORS_ORIGINS = ["http://localhost:3000"]
    
    # プロンプトテンプレート設定
    PROMPT_TEMPLATE_DIR = "src/llm/prompts/templates" 