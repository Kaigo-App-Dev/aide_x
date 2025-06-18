"""
test_preview_flow.py: 構成テンプレートのUIプレビュー動作テスト

このテストファイルは、構成テンプレートのプレビュー機能をテストします：
1. 新規テンプレートの作成
2. プレビュー表示の確認
3. フォーム送信の動作確認

テストは実際のHTTPリクエストを使用し、
プレビュー機能が正しく動作することを確認します。
"""

import sys
import os
import json
import pytest
from urllib.parse import urlparse
import re
import time

def test_preview_flow(client, test_structure_data):
    # 1. 新規テンプレート作成
    res = client.post("/structure/new", data=test_structure_data, follow_redirects=True)
    assert res.status_code == 200
    assert test_structure_data["title"] in res.data.decode("utf-8")

    # 2. 作成されたIDを取得（レスポンスのLocationヘッダーやリダイレクト先URLから）
    location = res.request.path
    if location and location.count("/") >= 2:
        created_id = location.split("/")[-1]
    else:
        # フォールバック: レスポンスHTML内にIDが含まれていれば抽出
        m = re.search(r'/preview/(\w+-\w+-\w+-\w+-\w+)', res.data.decode("utf-8"))
        created_id = m.group(1) if m else None
    assert created_id is not None

    # 3. 同期を待機（最大3秒）
    for _ in range(3):
        res = client.get("/preview")
        if res.status_code == 200:
            break
        time.sleep(1)

    # 4. プレビュー表示確認
    res2 = client.get(f"/preview/{created_id}")
    assert res2.status_code == 200
    assert "氏名" in res2.data.decode("utf-8")

    # 5. フォーム送信
    post_data = {
        "名前": "テスト太郎",
        "性別": "男性"
    }
    res3 = client.post(f"/preview/submit/{created_id}", data=post_data, follow_redirects=True)
    assert res3.status_code == 200
    assert "フォームが送信されました" in res3.data.decode("utf-8")

if __name__ == "__main__":
    pytest.main([__file__])
