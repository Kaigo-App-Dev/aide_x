import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.app import create_app
from src.structure.utils import save_structure, StructureDict
from uuid import uuid4

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_structure() -> StructureDict:
    structure_id = str(uuid4())
    structure: StructureDict = {
        "id": structure_id,
        "title": "テスト構造",
        "description": "これはテスト用の構造です",
        "content": {
            "sections": [{
                "title": "テストセクション",
                "description": "これは評価テストです。",
                "components": []
            }]
        },
        "metadata": None,
        "history": None
    }
    save_structure(structure_id, structure)
    return structure

def test_structure_list(client):
    response = client.get("/structure/list")
    assert response.status_code == 200
    assert "テンプレート" in response.data.decode("utf-8")  # ✅ Unicodeで比較

def test_preview_route(client):
    response = client.get("/preview/1234")  # 存在しないIDでも動作確認
    assert response.status_code in [200, 404]

def test_structure_evaluate(client, sample_structure):
    """構造体評価エンドポイントのテスト"""
    # 評価エンドポイントへのGETリクエスト
    response = client.get(f"/structure/evaluate/{sample_structure['id']}")
    
    # ステータスコードの確認
    assert response.status_code == 200, f"予期しないステータスコード: {response.status_code}"
    
    # レスポンスの内容確認
    data = response.get_json()
    assert data["status"] == "success", "status が 'success' ではありません"
