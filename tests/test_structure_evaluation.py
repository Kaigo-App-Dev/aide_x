"""
test_structure_evaluation.py: 構成全体に対する評価フローの統合テスト

このテストファイルは、構成評価の統合フローをテストします：
1. 新規構成の作成
2. 構成の整合性評価
3. 評価結果の表示

テストは実際のHTTPリクエストを使用し、
エンドツーエンドの評価フローが正しく機能することを確認します。
"""

import sys
import os
import json
import pytest
from urllib.parse import urlparse

def test_structure_evaluation(client, test_structure_data):
    # 新規構成テンプレートを登録
    res = client.post("/structure/new", data=test_structure_data, follow_redirects=True)
    assert res.status_code == 200
    assert test_structure_data["title"] in res.data.decode("utf-8")

    # ID取得
    created_id = res.request.path.split("/")[-1]
    assert created_id

    # 整合性評価ルートにアクセス
    res2 = client.get(f"/structure/evaluate/{created_id}")
    body = res2.data.decode("utf-8")
    assert res2.status_code == 200
    assert "intent_match" in body or "一致" in body  # スコアが表示されていればOK

if __name__ == "__main__":
    pytest.main([__file__])
