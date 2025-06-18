"""
環境変数管理モジュール
"""
import os
import sys
import logging
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# チェック対象の環境変数
REQUIRED_ENV_VARS = [
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY"
]

def mask_api_key(api_key: str) -> str:
    """
    APIキーをマスクして表示用の文字列を生成します。
    最初の4文字と最後の4文字のみを表示し、中間を...で置き換えます。
    
    Args:
        api_key: マスクするAPIキー
        
    Returns:
        マスクされたAPIキー文字列
    """
    if len(api_key) <= 8:
        return "***"  # 8文字以下の場合は全てマスク
    return f"{api_key[:4]}...{api_key[-4:]}"

def check_env_vars() -> Dict[str, Optional[str]]:
    """
    必要な環境変数が設定されているかチェックします。
    
    Returns:
        Dict[str, Optional[str]]: 環境変数名とその値の辞書
    """
    # .envファイルの読み込み
    load_dotenv()
    
    # 環境変数の状態を格納する辞書
    env_status = {}
    
    # 各環境変数をチェック
    for var_name in REQUIRED_ENV_VARS:
        value = os.getenv(var_name)
        env_status[var_name] = value
    
    return env_status

def print_env_status(env_status: Dict[str, Optional[str]]) -> None:
    """
    環境変数の状態を表示します。
    
    Args:
        env_status: 環境変数の状態を格納した辞書
    """
    missing_vars = []
    
    for var_name, value in env_status.items():
        if value:
            masked_value = mask_api_key(value)
            print(f"[OK] {var_name} = {masked_value}")
        else:
            print(f"[ERROR] MISSING: {var_name}")
            missing_vars.append(var_name)
    
    if missing_vars:
        raise EnvironmentError(
            f"以下の環境変数が未設定です: {', '.join(missing_vars)}"
        )

def check_environment() -> Tuple[bool, List[str]]:
    """
    環境変数の設定を確認する
    
    Returns:
        Tuple[bool, List[str]]: (成功したかどうか, エラーメッセージのリスト)
    """
    errors = []
    warnings = []
    
    # 必須の環境変数
    required_vars = [
        "FLASK_APP",
        "FLASK_ENV",
        "SECRET_KEY"
    ]
    
    # オプションの環境変数
    optional_vars = [
        "FLASK_DEBUG",
        "LOG_LEVEL",
        "GEMINI_API_KEY",
        "GCP_GEMINI_API_KEY",
        "USE_GCP_GEMINI",
        "GCP_PROJECT_ID"
    ]
    
    # 必須環境変数のチェック
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"必須の環境変数 {var} が設定されていません")
    
    # Gemini API設定のチェック
    use_gcp = os.getenv("USE_GCP_GEMINI", "0").lower() in ("1", "true", "yes")
    
    if use_gcp:
        # GCPモードの場合
        if not os.getenv("GCP_GEMINI_API_KEY"):
            errors.append("GCPモードが有効ですが、GCP_GEMINI_API_KEYが設定されていません")
        if not os.getenv("GCP_PROJECT_ID"):
            errors.append("GCPモードが有効ですが、GCP_PROJECT_IDが設定されていません")
        if os.getenv("GEMINI_API_KEY"):
            warnings.append("GCPモードが有効ですが、GEMINI_API_KEYも設定されています")
    else:
        # Developer APIモードの場合
        if not os.getenv("GEMINI_API_KEY"):
            errors.append("Developer APIモードが有効ですが、GEMINI_API_KEYが設定されていません")
        if os.getenv("GCP_GEMINI_API_KEY"):
            warnings.append("Developer APIモードが有効ですが、GCP_GEMINI_API_KEYも設定されています")
    
    # 警告メッセージの出力
    for warning in warnings:
        logger.warning(f"⚠️ {warning}")
    
    # エラーメッセージの出力
    for error in errors:
        logger.error(f"❌ {error}")
    
    return len(errors) == 0, errors

def get_environment_summary() -> Dict[str, str]:
    """
    環境変数の設定状況を取得する
    
    Returns:
        Dict[str, str]: 環境変数の設定状況
    """
    summary = {}
    
    # 基本設定
    summary["FLASK_APP"] = os.getenv("FLASK_APP", "未設定")
    summary["FLASK_ENV"] = os.getenv("FLASK_ENV", "未設定")
    summary["FLASK_DEBUG"] = os.getenv("FLASK_DEBUG", "未設定")
    summary["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "未設定")
    
    # Gemini API設定
    use_gcp = os.getenv("USE_GCP_GEMINI", "0").lower() in ("1", "true", "yes")
    summary["USE_GCP_GEMINI"] = "有効" if use_gcp else "無効"
    
    if use_gcp:
        summary["GCP_GEMINI_API_KEY"] = "設定済み" if os.getenv("GCP_GEMINI_API_KEY") else "未設定"
        summary["GCP_PROJECT_ID"] = os.getenv("GCP_PROJECT_ID", "未設定")
        summary["GEMINI_API_KEY"] = "設定済み" if os.getenv("GEMINI_API_KEY") else "未設定"
    else:
        summary["GEMINI_API_KEY"] = "設定済み" if os.getenv("GEMINI_API_KEY") else "未設定"
        summary["GCP_GEMINI_API_KEY"] = "設定済み" if os.getenv("GCP_GEMINI_API_KEY") else "未設定"
        summary["GCP_PROJECT_ID"] = os.getenv("GCP_PROJECT_ID", "未設定")
    
    return summary

def main() -> None:
    """
    メイン関数
    環境変数のチェックを実行し、結果を表示します。
    """
    try:
        print("🔍 環境変数のチェックを開始します...")
        env_status = check_env_vars()
        print_env_status(env_status)
        print("\n[OK] すべての環境変数が正しく設定されています。")
        
    except EnvironmentError as e:
        print(f"\n[ERROR] エラー: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 予期せぬエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 