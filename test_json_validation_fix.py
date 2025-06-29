#!/usr/bin/env python3
"""
JSONバリデーション修正のテストスクリプト
構成ID c7cf4b5e-3b0c-453d-8eb0-c03e188ab68b の問題を再現・検証
"""

import json
import logging
import sys
import os
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.files import extract_json_part, validate_json_string

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'test_json_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )
    return logging.getLogger(__name__)

def test_incomplete_json_detection():
    """不完全なJSONの検出テスト"""
    logger = setup_logging()
    logger.info("🔍 不完全なJSON検出テスト開始")
    
    # テストケース
    test_cases = [
        {
            "name": "開き括弧のみ",
            "input": "{",
            "expected_error": "不完全なJSON"
        },
        {
            "name": "閉じ括弧のみ",
            "input": "}",
            "expected_error": "不完全なJSON"
        },
        {
            "name": "開き括弧のみ（長い文字列）",
            "input": "{ \"title\": \"テスト\", \"description\": \"テスト説明\"",
            "expected_error": "不完全なJSON"
        },
        {
            "name": "閉じ括弧のみ（長い文字列）",
            "input": "\"title\": \"テスト\", \"description\": \"テスト説明\" }",
            "expected_error": "不完全なJSON"
        },
        {
            "name": "括弧の不均衡（開き括弧が多い）",
            "input": "{\"title\": \"テスト\", \"modules\": {\"module1\": {\"name\": \"テスト\"}",
            "expected_error": "括弧の不均衡"
        },
        {
            "name": "括弧の不均衡（閉じ括弧が多い）",
            "input": "\"title\": \"テスト\", \"modules\": {\"module1\": {\"name\": \"テスト\"}}}",
            "expected_error": "不完全なJSON"
        },
        {
            "name": "正常なJSON",
            "input": "{\"title\": \"テスト\", \"description\": \"テスト説明\"}",
            "expected_error": None
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for test_case in test_cases:
        logger.info(f"📋 テストケース: {test_case['name']}")
        
        try:
            # validate_json_stringでテスト
            result = validate_json_string(test_case['input'])
            
            if test_case['expected_error'] is None:
                # 正常なJSONの場合
                if result["is_valid"]:
                    logger.info(f"✅ 正常なJSON: 検証成功")
                    success_count += 1
                else:
                    logger.error(f"❌ 正常なJSONが失敗: {result['error']}")
            else:
                # エラーが期待される場合
                if not result["is_valid"] and test_case['expected_error'] in result['error']:
                    logger.info(f"✅ エラー検出成功: {result['error']}")
                    success_count += 1
                else:
                    logger.error(f"❌ エラー検出失敗: 期待={test_case['expected_error']}, 実際={result.get('error', 'なし')}")
        
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {e}")
    
    logger.info(f"📊 テスト結果: {success_count}/{total_count} 成功")
    return success_count == total_count

def test_extract_json_part():
    """extract_json_part関数のテスト"""
    logger = setup_logging()
    logger.info("🔍 extract_json_part関数テスト開始")
    
    # テストケース
    test_cases = [
        {
            "name": "不完全なJSON（開き括弧のみ）",
            "input": "以下は構成のJSONです：\n{",
            "expected_error": "不完全なJSON"
        },
        {
            "name": "不完全なJSON（閉じ括弧のみ）",
            "input": "以下は構成のJSONです：\n}",
            "expected_error": "不完全なJSON"
        },
        {
            "name": "正常なJSON（コードブロック内）",
            "input": "```json\n{\"title\": \"テスト\", \"description\": \"テスト説明\"}\n```",
            "expected_error": None
        },
        {
            "name": "正常なJSON（通常）",
            "input": "{\"title\": \"テスト\", \"description\": \"テスト説明\"}",
            "expected_error": None
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for test_case in test_cases:
        logger.info(f"📋 テストケース: {test_case['name']}")
        
        try:
            result = extract_json_part(test_case['input'])
            
            if test_case['expected_error'] is None:
                # 正常なJSONの場合
                if "error" not in result:
                    logger.info(f"✅ 正常なJSON: 抽出成功")
                    success_count += 1
                else:
                    logger.error(f"❌ 正常なJSONが失敗: {result['error']}")
            else:
                # エラーが期待される場合
                if "error" in result and test_case['expected_error'] in result['error']:
                    logger.info(f"✅ エラー検出成功: {result['error']}")
                    success_count += 1
                else:
                    logger.error(f"❌ エラー検出失敗: 期待={test_case['expected_error']}, 実際={result.get('error', 'なし')}")
        
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {e}")
    
    logger.info(f"📊 テスト結果: {success_count}/{total_count} 成功")
    return success_count == total_count

def test_real_structure_data():
    """実際の構造データでのテスト"""
    logger = setup_logging()
    logger.info("🔍 実際の構造データテスト開始")
    
    # 問題のあった構成ID
    structure_id = "c7cf4b5e-3b0c-453d-8eb0-c03e188ab68b"
    
    try:
        from src.structure.utils import load_structure_by_id
        structure = load_structure_by_id(structure_id)
        
        if not structure:
            logger.warning(f"⚠️ 構成ID {structure_id} が見つかりません")
            return False
        
        logger.info(f"📋 構成データ読み込み成功: {list(structure.keys())}")
        
        # structure["structure"]のテスト
        if "structure" in structure:
            structure_data = structure["structure"]
            logger.info(f"📋 structure['structure']の型: {type(structure_data)}")
            
            if isinstance(structure_data, str):
                logger.info(f"📋 structure['structure']の内容: {structure_data[:100]}...")
                
                # バリデーションテスト
                validation_result = validate_json_string(structure_data)
                if validation_result["is_valid"]:
                    logger.info("✅ structure['structure']のバリデーション成功")
                else:
                    logger.error(f"❌ structure['structure']のバリデーション失敗: {validation_result['error']}")
        
        # gemini_outputのテスト
        if "gemini_output" in structure:
            gemini_output = structure["gemini_output"]
            logger.info(f"📋 gemini_outputの型: {type(gemini_output)}")
            
            if isinstance(gemini_output, dict) and "content" in gemini_output:
                content = gemini_output["content"]
                logger.info(f"📋 gemini_output.contentの型: {type(content)}")
                
                if isinstance(content, str):
                    logger.info(f"📋 gemini_output.contentの内容: {content[:100]}...")
                    
                    # バリデーションテスト
                    validation_result = validate_json_string(content)
                    if validation_result["is_valid"]:
                        logger.info("✅ gemini_output.contentのバリデーション成功")
                    else:
                        logger.error(f"❌ gemini_output.contentのバリデーション失敗: {validation_result['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 実際の構造データテスト失敗: {e}")
        return False

def main():
    """メイン関数"""
    logger = setup_logging()
    logger.info("🚀 JSONバリデーション修正テスト開始")
    
    tests = [
        ("不完全なJSON検出テスト", test_incomplete_json_detection),
        ("extract_json_part関数テスト", test_extract_json_part),
        ("実際の構造データテスト", test_real_structure_data)
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"🧪 {test_name}開始")
        try:
            if test_func():
                logger.info(f"✅ {test_name}成功")
                success_count += 1
            else:
                logger.error(f"❌ {test_name}失敗")
        except Exception as e:
            logger.error(f"❌ {test_name}実行エラー: {e}")
    
    logger.info(f"📊 全体テスト結果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        logger.info("🎉 すべてのテストが成功しました！")
        return True
    else:
        logger.error("❌ 一部のテストが失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 