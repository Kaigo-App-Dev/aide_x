#!/usr/bin/env python3
"""
統合インターフェースのメッセージ送信をcURLでテストするスクリプト
"""

import requests
import json
import time
from datetime import datetime

def test_chat_message():
    """メッセージ送信をテスト"""
    
    # テスト設定
    base_url = "http://localhost:5000"
    structure_id = "test_unified_001"
    test_message = "こんにちは、cURLテストメッセージです"
    
    print(f"🧪 チャットメッセージ送信テスト開始")
    print(f"📋 構造ID: {structure_id}")
    print(f"📝 テストメッセージ: {test_message}")
    print(f"🌐 ベースURL: {base_url}")
    print("-" * 50)
    
    # 1. まずGETでページにアクセスしてCSRFトークンを取得
    print("1️⃣ ページアクセスしてCSRFトークンを取得...")
    try:
        response = requests.get(f"{base_url}/unified/{structure_id}")
        print(f"   📥 GET レスポンス: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ ページアクセス成功")
            # HTMLからCSRFトークンを抽出（簡易版）
            csrf_token = "test_token"  # 実際の実装ではHTMLパースが必要
        else:
            print(f"   ❌ ページアクセス失敗: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ ページアクセスエラー: {str(e)}")
        return False
    
    # 2. POSTでメッセージ送信
    print("\n2️⃣ メッセージ送信...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        }
        
        data = {
            'message': test_message
        }
        
        print(f"   📤 送信データ: {json.dumps(data, ensure_ascii=False)}")
        print(f"   📋 ヘッダー: {headers}")
        
        response = requests.post(
            f"{base_url}/unified/{structure_id}/chat",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"   📥 POST レスポンス: {response.status_code}")
        print(f"   📋 レスポンスヘッダー: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ 成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return True
            except json.JSONDecodeError:
                print(f"   ⚠️ JSONパース失敗: {response.text[:200]}")
                return False
        else:
            print(f"   ❌ エラー: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ タイムアウトエラー")
        return False
    except Exception as e:
        print(f"   ❌ 送信エラー: {str(e)}")
        return False

def test_evaluate():
    """評価実行をテスト"""
    
    base_url = "http://localhost:5000"
    structure_id = "test_unified_001"
    
    print(f"\n🧪 評価実行テスト")
    print("-" * 30)
    
    try:
        headers = {
            'X-CSRFToken': 'test_token'
        }
        
        response = requests.post(
            f"{base_url}/unified/{structure_id}/evaluate",
            headers=headers,
            timeout=60
        )
        
        print(f"📥 評価レスポンス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 評価成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 評価エラー: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 評価エラー: {str(e)}")
        return False

def test_save():
    """保存をテスト"""
    
    base_url = "http://localhost:5000"
    structure_id = "test_unified_001"
    
    print(f"\n🧪 保存テスト")
    print("-" * 20)
    
    try:
        headers = {
            'X-CSRFToken': 'test_token'
        }
        
        response = requests.post(
            f"{base_url}/unified/{structure_id}/save",
            headers=headers,
            timeout=30
        )
        
        print(f"📥 保存レスポンス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 保存成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 保存エラー: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 保存エラー: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    
    print("🚀 統合インターフェース cURL テスト開始")
    print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # テスト実行
    chat_success = test_chat_message()
    evaluate_success = test_evaluate()
    save_success = test_save()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    print(f"💬 メッセージ送信: {'✅ 成功' if chat_success else '❌ 失敗'}")
    print(f"📊 評価実行: {'✅ 成功' if evaluate_success else '❌ 失敗'}")
    print(f"💾 保存: {'✅ 成功' if save_success else '❌ 失敗'}")
    
    if all([chat_success, evaluate_success, save_success]):
        print("\n🎉 すべてのテストが成功しました！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
    
    print(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 