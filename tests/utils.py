"""
utils.py: テスト共通のユーティリティ関数

このファイルは、テスト間で共有される共通のユーティリティ関数を定義します：
- get_created_id: レスポンスから作成されたIDを取得
- assert_response_ok: レスポンスのステータスコードと内容を確認
- create_test_structure: テスト用の構成データを作成
"""

from typing import Dict, Any, Optional, Union
from flask.testing import FlaskClient

def get_created_id(response) -> Optional[str]:
    """レスポンスから作成されたIDを取得"""
    return response.request.path.split("/")[-1] if "/" in response.request.path else None

def assert_response_ok(client: FlaskClient, response, expected_title: str) -> None:
    """レスポンスのステータスコードと内容を確認"""
    assert response.status_code == 200
    assert expected_title in response.data.decode("utf-8")

def create_test_structure(title: str, description: str, content: Dict[str, Any]) -> Dict[str, Union[str, Dict[str, Any]]]:
    """テスト用の構成データを作成"""
    return {
        "title": title,
        "description": description,
        "content": content
    } 