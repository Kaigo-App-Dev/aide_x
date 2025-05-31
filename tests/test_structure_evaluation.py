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

def test_structure_evaluation(client):
    # 異常構成テンプレートを登録
    structure_data = {
        "title": "評価用テンプレート",
        "description": "整合性チェックテスト",
        "content": json.dumps({
            "sections": [
                { "name": "名前", "type": "text" },
                { "name": "不明", "type": "unknown_type" }  # ← 整合性エラー対象
            ]
        })
    }

    res = client.post("/structure/new", data=structure_data, follow_redirects=True)
    assert res.status_code == 200
    assert "評価用テンプレート" in res.data.decode("utf-8")

    # ID取得
    from urllib.parse import urlparse
    created_id = res.request.path.split("/")[-1]
    assert created_id

    # 整合性評価ルートにアクセス
    res2 = client.get(f"/structure/evaluate/{created_id}")
    body = res2.data.decode("utf-8")
    assert res2.status_code == 200
    assert "intent_match" in body or "一致" in body  # スコアが表示されていればOK
