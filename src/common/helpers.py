"""
共通ユーティリティ関数モジュール
"""
import datetime
import re
from typing import Any, Dict, List, Optional, Union
from markupsafe import Markup

def format_datetime(dt: datetime.datetime, format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """日時を指定フォーマットで文字列に変換"""
    return dt.strftime(format)

def format_date(date: datetime.date, format: str = '%Y-%m-%d') -> str:
    """日付を指定フォーマットで文字列に変換"""
    return date.strftime(format)

def format_number(number: Union[int, float], decimal_places: int = 2) -> str:
    """数値を3桁区切りでフォーマット"""
    if isinstance(number, float):
        return f"{number:,.{decimal_places}f}"
    return f"{number:,}"

def truncate_text(text: str, length: int = 100, suffix: str = '...') -> str:
    """テキストを指定長さで切り詰め"""
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix

def nl2br(text: str) -> Markup:
    """改行を<br>タグに変換"""
    if not text:
        return Markup('')
    return Markup(text.replace('\n', '<br>'))

def get_pagination_info(page: int, per_page: int, total: int) -> Dict[str, Any]:
    """ページネーション情報を生成"""
    total_pages = (total + per_page - 1) // per_page
    return {
        'current_page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }

def generate_slug(text: str) -> str:
    """テキストからスラッグを生成"""
    # 小文字に変換
    text = text.lower()
    # 日本語をローマ字に変換（必要に応じて）
    # 特殊文字を除去
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # スペースをハイフンに変換
    text = re.sub(r'\s+', '-', text)
    # 連続するハイフンを1つに
    text = re.sub(r'-+', '-', text)
    # 先頭と末尾のハイフンを除去
    return text.strip('-')

def get_file_extension(filename: str) -> str:
    """ファイル名から拡張子を取得"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def is_safe_filename(filename: str) -> bool:
    """ファイル名が安全かチェック"""
    # 危険な文字を含まないかチェック
    dangerous_chars = r'[<>:"/\\|?*]'
    return not bool(re.search(dangerous_chars, filename))

def format_file_size(size_in_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB" 