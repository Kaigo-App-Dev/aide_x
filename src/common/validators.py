"""
入力値検証モジュール
"""
import re
from typing import Optional, List, Dict, Any

def is_valid_email(email: str) -> bool:
    """メールアドレスの形式チェック"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_password(password: str) -> bool:
    """
    パスワードの強度チェック
    - 8文字以上
    - 大文字・小文字・数字を含む
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

def is_valid_username(username: str) -> bool:
    """
    ユーザー名の形式チェック
    - 3-20文字
    - 英数字とアンダースコアのみ
    """
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username))

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[str]:
    """
    必須フィールドの存在チェック
    エラーがある場合はエラーメッセージを返す
    """
    for field in required_fields:
        if field not in data or not data[field]:
            return f"{field}は必須項目です。"
    return None

def sanitize_input(text: str) -> str:
    """
    入力テキストのサニタイズ
    - HTMLタグの除去
    - 特殊文字のエスケープ
    """
    # HTMLタグの除去
    text = re.sub(r'<[^>]+>', '', text)
    # 特殊文字のエスケープ
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text

def validate_length(text: str, min_length: int = 0, max_length: int = None) -> bool:
    """
    テキストの長さチェック
    """
    if len(text) < min_length:
        return False
    if max_length and len(text) > max_length:
        return False
    return True 