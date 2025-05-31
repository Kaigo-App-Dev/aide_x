import sys
import os
import json
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_preview_flow(client):
    # 1. 新規テンプレート作成
    new_structure = {
        "title": "テストフォーム",
        "description": "自動テスト用",
        "content": json.dumps({
            "title": "テストフォーム",
            "sections": [
                { "name": "名前", "type": "text", "label": "氏名" },
                { "name": "性別", "type": "select", "label": "性別", "options": ["男性", "女性"] }
            ]
        })
    }

    res = client.post("/structure/new", data=new_structure, follow_redirects=True)
    assert res.status_code == 200
    assert "テストフォーム" in res.data.decode("utf-8")

    # 2. 作成されたIDを取得（最後のURLから）
    from urllib.parse import urlparse
    last_url = res.request.path
    created_id = last_url.split("/")[-1] if "/" in last_url else None
    assert created_id is not None

    # 3. プレビュー表示確認
    res2 = client.get(f"/preview/{created_id}")
    assert res2.status_code == 200
    assert "氏名" in res2.data.decode("utf-8")

    # 4. フォーム送信
    post_data = {
        "名前": "テスト太郎",
        "性別": "男性"
    }
    res3 = client.post(f"/preview/submit/{created_id}", data=post_data, follow_redirects=True)
    assert res3.status_code == 200
    assert "フォームが送信されました" in res3.data.decode("utf-8")
