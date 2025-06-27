#!/usr/bin/env python3
"""
古い構成ファイルのメッセージに source フィールドを補完するマイグレーションスクリプト

使用方法:
    python tools/migrate_legacy_messages.py

機能:
    - structures/ 以下の .json ファイルを走査
    - messages 配列の各メッセージに source がなければ "chat" を補完
    - 元のファイルは .json.bak にバックアップ
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import sys

def migrate_legacy_messages():
    """古い構成ファイルのメッセージに source フィールドを補完する"""
    
    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent
    structures_dir = project_root / "structures"
    
    if not structures_dir.exists():
        print(f"❌ structures ディレクトリが見つかりません: {structures_dir}")
        return False
    
    print(f"🔍 structures ディレクトリを走査中: {structures_dir}")
    
    # JSONファイルを検索
    json_files = list(structures_dir.glob("*.json"))
    
    if not json_files:
        print("❌ JSONファイルが見つかりませんでした")
        return False
    
    print(f"📁 処理対象ファイル数: {len(json_files)}")
    
    migrated_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            print(f"\n📄 処理中: {json_file.name}")
            
            # ファイルを読み込み
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # バックアップを作成
            backup_file = json_file.with_suffix('.json.bak')
            shutil.copy2(json_file, backup_file)
            print(f"💾 バックアップ作成: {backup_file.name}")
            
            # messages 配列を確認
            messages = data.get('messages', [])
            if not messages:
                print(f"ℹ️ メッセージがありません: {json_file.name}")
                continue
            
            print(f"💬 メッセージ数: {len(messages)}")
            
            # 各メッセージに source フィールドを補完
            updated = False
            for i, message in enumerate(messages):
                if isinstance(message, dict) and 'source' not in message:
                    # source フィールドが存在しない場合、role に基づいて補完
                    if message.get('role') == 'user':
                        message['source'] = 'chat'
                    elif message.get('role') == 'assistant':
                        # Claude評価メッセージかどうかを判定
                        content = message.get('content', '')
                        if 'Claude評価結果' in content or message.get('type') == 'claude_eval':
                            message['source'] = 'claude'
                        else:
                            message['source'] = 'chat'
                    else:
                        message['source'] = 'chat'
                    
                    updated = True
                    print(f"  ✅ メッセージ {i+1}: source='{message['source']}' を追加")
            
            if updated:
                # 更新されたファイルを保存
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                migrated_count += 1
                print(f"✅ マイグレーション完了: {json_file.name}")
            else:
                print(f"ℹ️ 更新不要: {json_file.name}")
                # バックアップファイルを削除（更新不要の場合）
                backup_file.unlink()
                
        except Exception as e:
            error_count += 1
            print(f"❌ エラー: {json_file.name} - {str(e)}")
            continue
    
    # 結果を表示
    print(f"\n🎉 マイグレーション完了!")
    print(f"📊 処理結果:")
    print(f"  - 処理対象ファイル: {len(json_files)}")
    print(f"  - マイグレーション完了: {migrated_count}")
    print(f"  - エラー: {error_count}")
    
    if migrated_count > 0:
        print(f"\n💡 バックアップファイルは .json.bak 拡張子で保存されています")
        print(f"💡 問題がなければ、バックアップファイルを削除できます")
    
    return error_count == 0

def main():
    """メイン関数"""
    print("🔄 古い構成ファイルのメッセージマイグレーションを開始します...")
    
    try:
        success = migrate_legacy_messages()
        if success:
            print("\n✅ マイグレーションが正常に完了しました!")
            sys.exit(0)
        else:
            print("\n⚠️ マイグレーション中にエラーが発生しました")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 