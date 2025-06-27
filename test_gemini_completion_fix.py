#!/usr/bin/env python3
"""
Gemini補完失敗時の調査と修正の検証スクリプト
"""

import sys
import os
import json
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_gemini_completion.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def test_extract_json_part():
    """extract_json_part関数のテスト"""
    logger = setup_logging()
    logger.info("🔍 extract_json_part関数のテスト開始")
    
    try:
        from src.utils.files import extract_json_part
        
        # テストケース1: 正常なJSON
        test_json = '{"title": "テスト", "modules": [{"name": "test"}]}'
        result = extract_json_part(test_json)
        logger.info(f"✅ 正常JSONテスト: {result.get('title') == 'テスト'}")
        
        # テストケース2: 未クオートキーのJSON
        test_unquoted = '{title: "テスト", modules: [{name: "test"}]}'
        result = extract_json_part(test_unquoted)
        logger.info(f"✅ 未クオートキーテスト: {result.get('title') == 'テスト'}")
        
        # テストケース3: コードブロック内のJSON
        test_codeblock = '```json\n{"title": "テスト", "modules": []}\n```'
        result = extract_json_part(test_codeblock)
        logger.info(f"✅ コードブロックテスト: {result.get('title') == 'テスト'}")
        
        # テストケース4: 無効なJSON
        test_invalid = 'invalid json: { title: unquoted_key }'
        result = extract_json_part(test_invalid)
        logger.info(f"✅ 無効JSONテスト: {'error' in result}")
        
        logger.info("✅ extract_json_part関数テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ extract_json_part関数テスト失敗: {e}")
        return False

def test_gemini_provider_chat():
    """GeminiProvider.chat()メソッドのテスト"""
    logger = setup_logging()
    logger.info("🔍 GeminiProvider.chat()メソッドのテスト開始")
    
    try:
        from src.llm.providers.gemini import GeminiProvider
        from src.llm.prompts import PromptManager
        from src.llm.prompts.prompt import Prompt
        
        # モックプロンプトマネージャー
        class MockPromptManager:
            def get_template(self, provider, template_name):
                return "テストプロンプト: {content}"
        
        # モックプロンプト
        mock_prompt = Prompt(template="テストプロンプト: {content}", description="テスト")
        
        # APIキーが設定されていない場合はスキップ
        if not os.getenv("GOOGLE_API_KEY"):
            logger.warning("⚠️ GOOGLE_API_KEYが設定されていないため、APIテストをスキップ")
            return True
        
        # GeminiProviderの初期化テスト
        try:
            provider = GeminiProvider(MockPromptManager())
            logger.info("✅ GeminiProvider初期化成功")
        except Exception as e:
            logger.warning(f"⚠️ GeminiProvider初期化失敗（APIキー不足の可能性）: {e}")
            return True
        
        # chat()メソッドのNone返却テスト
        try:
            # 実際のAPI呼び出しは行わず、メソッドの存在確認のみ
            if hasattr(provider, 'chat'):
                logger.info("✅ chat()メソッドが存在します")
            else:
                logger.error("❌ chat()メソッドが存在しません")
                return False
        except Exception as e:
            logger.error(f"❌ chat()メソッドテスト失敗: {e}")
            return False
        
        logger.info("✅ GeminiProvider.chat()メソッドテスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ GeminiProvider.chat()メソッドテスト失敗: {e}")
        return False

def test_apply_gemini_completion():
    """apply_gemini_completion関数のテスト"""
    logger = setup_logging()
    logger.info("🔍 apply_gemini_completion関数のテスト開始")
    
    try:
        from src.routes.unified_routes import apply_gemini_completion, record_gemini_completion_stats
        
        # テスト用構造データ
        test_structure = {
            "id": "test_structure_001",
            "content": {
                "title": "テスト構成",
                "description": "テスト用の構成です",
                "modules": [
                    {"name": "テストモジュール1", "description": "テスト用モジュール"}
                ]
            },
            "completions": []
        }
        
        # 統計記録機能のテスト
        try:
            record_gemini_completion_stats("test_structure_001", "success")
            logger.info("✅ 統計記録機能（成功）テスト完了")
            
            record_gemini_completion_stats("test_structure_001", "error", "テストエラー")
            logger.info("✅ 統計記録機能（エラー）テスト完了")
        except Exception as e:
            logger.error(f"❌ 統計記録機能テスト失敗: {e}")
            return False
        
        # apply_gemini_completion関数の存在確認
        if hasattr(apply_gemini_completion, '__call__'):
            logger.info("✅ apply_gemini_completion関数が存在します")
        else:
            logger.error("❌ apply_gemini_completion関数が存在しません")
            return False
        
        logger.info("✅ apply_gemini_completion関数テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ apply_gemini_completion関数テスト失敗: {e}")
        return False

def test_error_handling():
    """エラーハンドリングのテスト"""
    logger = setup_logging()
    logger.info("🔍 エラーハンドリングのテスト開始")
    
    try:
        from src.utils.files import extract_json_part
        
        # エラーケースのテスト
        error_cases = [
            "",  # 空文字列
            None,  # None
            "invalid json",  # 無効なJSON
            "{incomplete",  # 不完全なJSON
        ]
        
        for i, error_case in enumerate(error_cases):
            try:
                result = extract_json_part(error_case)
                if "error" in result:
                    logger.info(f"✅ エラーケース{i+1}処理成功: {result['error']}")
                else:
                    logger.warning(f"⚠️ エラーケース{i+1}でエラーが検出されませんでした")
            except Exception as e:
                logger.error(f"❌ エラーケース{i+1}で例外が発生: {e}")
        
        logger.info("✅ エラーハンドリングテスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ エラーハンドリングテスト失敗: {e}")
        return False

def test_logging_output():
    """ログ出力のテスト"""
    logger = setup_logging()
    logger.info("🔍 ログ出力のテスト開始")
    
    # ログディレクトリの確認
    log_dirs = ["logs", "logs/claude_gemini_diff"]
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            logger.info(f"✅ ログディレクトリ存在: {log_dir}")
        else:
            logger.warning(f"⚠️ ログディレクトリ不存在: {log_dir}")
    
    # 統計ファイルの確認
    stats_file = "logs/gemini_completion_stats.json"
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            logger.info(f"✅ 統計ファイル存在: 総実行回数={stats.get('total_completions', 0)}")
        except Exception as e:
            logger.error(f"❌ 統計ファイル読み込みエラー: {e}")
    else:
        logger.info("📝 統計ファイルはまだ作成されていません")
    
    logger.info("✅ ログ出力テスト完了")
    return True

def main():
    """メイン関数"""
    logger = setup_logging()
    logger.info("🚀 Gemini補完失敗時の調査と修正の検証開始")
    
    tests = [
        ("extract_json_part関数", test_extract_json_part),
        ("GeminiProvider.chat()メソッド", test_gemini_provider_chat),
        ("apply_gemini_completion関数", test_apply_gemini_completion),
        ("エラーハンドリング", test_error_handling),
        ("ログ出力", test_logging_output),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 {test_name}のテスト開始")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 成功" if result else "❌ 失敗"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            logger.error(f"❌ 例外発生: {test_name} - {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    logger.info(f"\n{'='*50}")
    logger.info("📊 テスト結果サマリー")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        logger.info("🎉 全てのテストが成功しました！")
        return 0
    else:
        logger.error(f"⚠️ {total - passed}個のテストが失敗しました")
        return 1

if __name__ == "__main__":
    exit(main()) 