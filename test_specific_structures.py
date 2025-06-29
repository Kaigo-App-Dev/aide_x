#!/usr/bin/env python3
"""
特定の構成IDをテストするスクリプト（修正版）
"""

import json
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.files import extract_json_part, validate_json_string, repair_unquoted_keys
from src.common.logging_utils import setup_logging

def test_structure_extraction(structure_id: str):
    """特定の構成IDの抽出処理をテスト"""
    print(f"🔍 構成ID {structure_id} のテスト開始")
    
    # データファイルのパスを構築
    data_paths = [
        f"data/{structure_id}.json",
        f"structures/{structure_id}.json"
    ]
    
    structure_data = None
    used_path = None
    
    # データファイルを検索
    for path in data_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    structure_data = json.load(f)
                used_path = path
                print(f"✅ データファイル読み込み成功: {path}")
                break
            except Exception as e:
                print(f"❌ データファイル読み込み失敗 {path}: {e}")
    
    if not structure_data:
        print(f"❌ 構成ID {structure_id} のデータファイルが見つかりません")
        return
    
    print(f"📁 使用ファイル: {used_path}")
    
    # 構造データの分析
    print("\n📊 構造データ分析:")
    print(f"  - データ型: {type(structure_data)}")
    print(f"  - キー数: {len(structure_data)}")
    print(f"  - キー一覧: {list(structure_data.keys())}")
    
    # 各フィールドの詳細分析
    for key, value in structure_data.items():
        print(f"\n🔍 フィールド '{key}':")
        print(f"  - 型: {type(value)}")
        print(f"  - 値の長さ: {len(str(value)) if value else 0}")
        
        if isinstance(value, str):
            print(f"  - 文字列内容（最初の200文字）: {repr(value[:200])}")
            
            # 不完全なJSONの検出
            if value.strip() == "{}":
                print("  ⚠️  空のJSONオブジェクトを検出")
            elif value.strip() == "{":
                print("  ❌ 不完全なJSON（開き括弧のみ）を検出")
            elif value.strip() == "}":
                print("  ❌ 不完全なJSON（閉じ括弧のみ）を検出")
            elif value.strip().startswith("{") and not value.strip().endswith("}"):
                print("  ❌ 不完全なJSON（閉じ括弧不足）を検出")
            elif not value.strip().startswith("{") and value.strip().endswith("}"):
                print("  ❌ 不完全なJSON（開き括弧不足）を検出")
            
            # 括弧の均衡チェック
            open_braces = value.count('{')
            close_braces = value.count('}')
            if open_braces != close_braces:
                print(f"  ❌ 括弧の不均衡: 開き括弧{open_braces}個、閉じ括弧{close_braces}個")
            
            # 未クオートキーの検出
            unquoted_patterns = [
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:',  # 通常の未クオートキー
                r'([「」\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+)\s*:',  # 日本語未クオートキー
                r'([^\s:,\{\}\[\]"]+)\s*:'  # 特殊文字を含む未クオートキー
            ]
            
            import re
            for pattern in unquoted_patterns:
                matches = re.findall(pattern, value)
                if matches:
                    print(f"  ⚠️  未クオートキーを検出: {matches}")
    
    # extract_json_part関数のテスト
    print(f"\n🧪 extract_json_part関数のテスト:")
    
    # テスト対象のテキストを決定
    test_texts = []
    
    if 'structure' in structure_data and structure_data['structure']:
        test_texts.append(('structure', structure_data['structure']))
    
    if 'gemini_output' in structure_data and structure_data['gemini_output']:
        test_texts.append(('gemini_output', structure_data['gemini_output']))
    
    if 'content' in structure_data and structure_data['content']:
        test_texts.append(('content', structure_data['content']))
    
    for field_name, text in test_texts:
        print(f"\n📝 {field_name}フィールドのテスト:")
        
        if isinstance(text, str):
            print(f"  - テキスト長: {len(text)}")
            print(f"  - テキスト内容（最初の300文字）: {repr(text[:300])}")
            
            # repair_unquoted_keys関数のテスト
            print(f"\n🔧 repair_unquoted_keys関数のテスト:")
            try:
                repaired_text = repair_unquoted_keys(text)
                if repaired_text != text:
                    print(f"  ✅ 修復が実行されました")
                    print(f"  - 修復前: {repr(text[:200])}")
                    print(f"  - 修復後: {repr(repaired_text[:200])}")
                else:
                    print(f"  ✅ 修復は不要でした")
            except Exception as e:
                print(f"  ❌ 修復処理でエラー: {e}")
            
            # extract_json_part関数のテスト
            print(f"\n🔍 extract_json_part関数のテスト:")
            try:
                result = extract_json_part(text)
                print(f"  - 結果型: {type(result)}")
                
                if isinstance(result, dict):
                    if 'error' in result:
                        print(f"  ❌ エラーが発生: {result['error']}")
                        if 'reason' in result:
                            print(f"  - 理由: {result['reason']}")
                        if 'original_text' in result:
                            print(f"  - 元テキスト: {result['original_text'][:200]}...")
                    else:
                        print(f"  ✅ 正常に抽出されました")
                        print(f"  - 抽出されたキー: {list(result.keys())}")
                        print(f"  - 抽出された内容: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
                else:
                    print(f"  ⚠️  予期しない結果型: {result}")
                    
            except Exception as e:
                print(f"  ❌ extract_json_partでエラー: {e}")
                import traceback
                traceback.print_exc()
    
    # validate_json_string関数のテスト
    print(f"\n✅ validate_json_string関数のテスト:")
    
    for field_name, text in test_texts:
        if isinstance(text, str):
            print(f"\n📝 {field_name}フィールドのJSONバリデーション:")
            
            # 修復前のバリデーション
            validation_before = validate_json_string(text)
            print(f"  - 修復前: {'✅ 有効' if validation_before['is_valid'] else '❌ 無効'}")
            if not validation_before['is_valid']:
                print(f"    - エラー: {validation_before['error']}")
            
            # 修復後のバリデーション
            try:
                repaired_text = repair_unquoted_keys(text)
                validation_after = validate_json_string(repaired_text)
                print(f"  - 修復後: {'✅ 有効' if validation_after['is_valid'] else '❌ 無効'}")
                if not validation_after['is_valid']:
                    print(f"    - エラー: {validation_after['error']}")
                else:
                    print(f"    - 修復により有効なJSONになりました")
            except Exception as e:
                print(f"  - 修復処理でエラー: {e}")

def main():
    """メイン関数"""
    # ログ設定
    setup_logging()
    
    if len(sys.argv) != 2:
        print("使用方法: python test_specific_structures.py <structure_id>")
        print("例: python test_specific_structures.py eeab3b98-e029-4650-b207-576ba1e47007")
        sys.exit(1)
    
    structure_id = sys.argv[1]
    test_structure_extraction(structure_id)

if __name__ == "__main__":
    main() 