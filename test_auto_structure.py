#!/usr/bin/env python3
"""
自動構成生成・評価・UIプレビューシステムのテストスクリプト
"""

import requests
import json
import time

def test_auto_structure_system():
    """自動構成生成・評価・UIプレビューシステムをテストする"""
    
    base_url = "http://localhost:5000"
    structure_id = "test_unified_001"
    
    print("🧪 自動構成生成・評価・UIプレビューシステムのテスト開始")
    print(f"📡 ベースURL: {base_url}")
    print(f"🆔 構成ID: {structure_id}")
    print("-" * 50)
    
    # 1. 初期構成内容を取得
    print("1️⃣ 初期構成内容を取得...")
    try:
        response = requests.get(f"{base_url}/unified/api/structure_content/{structure_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 初期構成取得成功: {len(data.get('content', {}))} 個の要素")
            print(f"   - UI準備状態: {data.get('ui_ready', False)}")
        else:
            print(f"❌ 初期構成取得失敗: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 初期構成取得エラー: {e}")
        return
    
    # 2. チャットメッセージを送信（UI構成生成をトリガー）
    print("\n2️⃣ チャットメッセージを送信（UI構成生成をトリガー）...")
    test_message = "React + TypeScript + Tailwind CSSを使用したモダンなブログシステムのUI構成を作成してください。ヘッダー、ナビゲーション、メインコンテンツ、サイドバー、フッターを含むレスポンシブデザインで、ダークモード対応もお願いします。"
    
    try:
        response = requests.post(
            f"{base_url}/unified/{structure_id}/chat",
            json={"message": test_message},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ チャット送信成功")
            print(f"   - 成功: {data.get('success')}")
            print(f"   - 構成変更: {data.get('content_changed')}")
            print(f"   - UI準備状態: {data.get('ui_ready')}")
            print(f"   - メッセージ数: {len(data.get('messages', []))}")
            
            if data.get('content_changed'):
                print("🎉 構成が自動生成されました！")
                content = data.get('content', {})
                print(f"   - タイトル: {content.get('title', 'N/A')}")
                print(f"   - 説明: {content.get('description', 'N/A')[:50]}...")
                print(f"   - 構成要素数: {len(content.get('content', {}))}")
                
                if data.get('ui_ready'):
                    print("🎨 UI準備完了！プレビューが利用可能です")
                else:
                    print("ℹ️ UI準備未完了 - より詳細なUI構成を指定してください")
            else:
                print("ℹ️ 構成に変更はありませんでした")
        else:
            print(f"❌ チャット送信失敗: {response.status_code}")
            print(f"   レスポンス: {response.text}")
            return
    except Exception as e:
        print(f"❌ チャット送信エラー: {e}")
        return
    
    # 3. ポーリングAPIをテスト
    print("\n3️⃣ ポーリングAPIをテスト...")
    try:
        response = requests.get(f"{base_url}/unified/api/structure_content/{structure_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ポーリングAPI成功")
            print(f"   - 成功: {data.get('success')}")
            print(f"   - 構成要素数: {len(data.get('content', {}))}")
            print(f"   - UI準備状態: {data.get('ui_ready')}")
        else:
            print(f"❌ ポーリングAPI失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ポーリングAPIエラー: {e}")
    
    # 4. UIプレビューAPIをテスト
    print("\n4️⃣ UIプレビューAPIをテスト...")
    try:
        response = requests.get(f"{base_url}/preview/{structure_id}")
        if response.status_code == 200:
            print(f"✅ UIプレビューAPI成功")
            print(f"   - レスポンスサイズ: {len(response.text)} 文字")
            print(f"   - HTML含む: {'<html' in response.text.lower()}")
            print(f"   - スタイル含む: {'<style' in response.text.lower()}")
        else:
            print(f"❌ UIプレビューAPI失敗: {response.status_code}")
            print(f"   レスポンス: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ UIプレビューAPIエラー: {e}")
    
    print("\n🎯 テスト完了")
    print("💡 ブラウザで http://localhost:5000/unified/test_unified_001 にアクセスして動作を確認してください")
    print("🎨 UIプレビューは右側のペインで確認できます")

if __name__ == "__main__":
    test_auto_structure_system() 