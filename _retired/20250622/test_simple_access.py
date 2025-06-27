#!/usr/bin/env python3
"""
シンプルな統合インターフェースアクセステスト
"""

import requests
import time

def test_unified_access():
    """統合インターフェースへのアクセステスト"""
    base_url = "http://localhost:5000"
    structure_id = "test_unified_001"
    
    print("🧪 統合インターフェースアクセステスト開始")
    print("=" * 50)
    
    # 1. 基本的なアクセステスト
    print(f"📡 テスト: /unified/{structure_id} へのアクセス")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/unified/{structure_id}", timeout=10)
        end_time = time.time()
        
        print(f"✅ レスポンス受信: {response.status_code}")
        print(f"⏱️  応答時間: {end_time - start_time:.2f}秒")
        print(f"📏 レスポンスサイズ: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("🎉 アクセス成功！")
            
            # HTMLの内容を確認
            content = response.text
            if "統合インターフェース" in content:
                print("✅ HTML内容確認: 統合インターフェースのタイトルを検出")
            else:
                print("⚠️  HTML内容確認: 統合インターフェースのタイトルが見つかりません")
            
            if "test_unified_001" in content:
                print("✅ HTML内容確認: 構成IDを検出")
            else:
                print("⚠️  HTML内容確認: 構成IDが見つかりません")
                
            # レスポンスの最初の500文字を表示
            print(f"📄 レスポンス内容（最初の500文字）:")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
                
        elif response.status_code == 404:
            print("❌ 404エラー: 構成ファイルが見つかりません")
            print(f"エラー内容: {response.text[:200]}...")
        elif response.status_code == 500:
            print("❌ 500エラー: サーバーエラーが発生しました")
            print(f"エラー内容: {response.text[:200]}...")
        else:
            print(f"❌ 予期しないステータスコード: {response.status_code}")
            print(f"レスポンス内容: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: Flaskアプリが起動していません")
        print("💡 解決方法: python -m src.app を実行してください")
    except requests.exceptions.Timeout:
        print("❌ タイムアウト: 応答が10秒以内に返されませんでした")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
    
    print("\n" + "=" * 50)
    print("✅ テスト完了")

if __name__ == "__main__":
    test_unified_access() 