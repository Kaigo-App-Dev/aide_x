import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from main import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_structure_list(client):
    response = client.get("/structure/list")
    assert response.status_code == 200
    assert "テンプレート" in response.data.decode("utf-8")  # ✅ Unicodeで比較

def test_preview_route(client):
    response = client.get("/preview/1234")  # 存在しないIDでも動作確認
    assert response.status_code in [200, 404]
