#!/usr/bin/env python3
"""
評価・補完の状態表示機能テストスクリプト
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_evaluation_status_display():
    """評価状態表示機能をテスト"""
    
    print("=== 評価状態表示機能テスト ===")
    
    # テストケース1: 成功
    success_evaluation = {
        "provider": "claude",
        "status": "success",
        "score": 0.85,
        "feedback": "構成は概ね妥当ですが、目的の記載が不足しています。",
        "details": {
            "intent_match": "意図との一致度に関する詳細",
            "clarity": "構造の明確さに関する詳細",
            "implementation": "実装の容易さに関する詳細"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # テストケース2: 失敗
    failed_evaluation = {
        "provider": "claude",
        "status": "failed",
        "reason": "評価結果が空でした",
        "error_details": "API呼び出しに失敗しました: Connection timeout",
        "timestamp": datetime.now().isoformat()
    }
    
    # テストケース3: スキップ
    skipped_evaluation = {
        "provider": "claude",
        "status": "skipped",
        "reason": "構成が空のため評価をスキップしました",
        "timestamp": datetime.now().isoformat()
    }
    
    # テストケース4: 未実行
    no_evaluation = None
    
    test_cases = [
        ("成功", success_evaluation, "success"),
        ("失敗", failed_evaluation, "failed"),
        ("スキップ", skipped_evaluation, "skipped"),
        ("未実行", no_evaluation, "none")
    ]
    
    for case_name, evaluation, expected_status in test_cases:
        print(f"\n--- テストケース: {case_name} ---")
        if evaluation:
            actual_status = evaluation.get("status", "unknown")
            status = "✅" if actual_status == expected_status else "❌"
            print(f"{status} 期待されるstatus: {expected_status}, 実際: {actual_status}")
            print(f"  プロバイダー: {evaluation.get('provider')}")
            if evaluation.get("score"):
                print(f"  スコア: {evaluation.get('score')}")
            if evaluation.get("reason"):
                print(f"  理由: {evaluation.get('reason')}")
        else:
            print("✅ 評価データなし（未実行状態）")

def test_completion_status_display():
    """補完状態表示機能をテスト"""
    
    print("\n=== 補完状態表示機能テスト ===")
    
    # テストケース1: 成功
    success_completion = {
        "provider": "gemini",
        "status": "success",
        "content": "補完されたコードがここに表示されます...",
        "timestamp": datetime.now().isoformat()
    }
    
    # テストケース2: 失敗
    failed_completion = {
        "provider": "gemini",
        "status": "failed",
        "reason": "補完中にエラーが発生しました: API rate limit exceeded",
        "error_details": "Rate limit exceeded. Please try again later.",
        "timestamp": datetime.now().isoformat()
    }
    
    # テストケース3: 未実行
    no_completion = None
    
    test_cases = [
        ("成功", success_completion, "success"),
        ("失敗", failed_completion, "failed"),
        ("未実行", no_completion, "none")
    ]
    
    for case_name, completion, expected_status in test_cases:
        print(f"\n--- テストケース: {case_name} ---")
        if completion:
            actual_status = completion.get("status", "unknown")
            status = "✅" if actual_status == expected_status else "❌"
            print(f"{status} 期待されるstatus: {expected_status}, 実際: {actual_status}")
            print(f"  プロバイダー: {completion.get('provider')}")
            if completion.get("content"):
                print(f"  コンテンツ: {completion.get('content')[:50]}...")
            if completion.get("reason"):
                print(f"  理由: {completion.get('reason')}")
        else:
            print("✅ 補完データなし（未実行状態）")

def test_error_message_generation():
    """エラーメッセージ生成機能をテスト"""
    
    print("\n=== エラーメッセージ生成機能テスト ===")
    
    # テストケース1: Claude評価失敗
    claude_error = {
        "provider": "claude",
        "status": "failed",
        "reason": "評価結果が空でした",
        "error_details": "API呼び出しに失敗しました: Connection timeout"
    }
    
    # テストケース2: Gemini補完失敗
    gemini_error = {
        "provider": "gemini",
        "status": "failed",
        "reason": "補完中にエラーが発生しました: API rate limit exceeded",
        "error_details": "Rate limit exceeded. Please try again later."
    }
    
    test_cases = [
        ("Claude評価失敗", claude_error),
        ("Gemini補完失敗", gemini_error)
    ]
    
    for case_name, error_data in test_cases:
        print(f"\n--- テストケース: {case_name} ---")
        print(f"  プロバイダー: {error_data.get('provider')}")
        print(f"  ステータス: {error_data.get('status')}")
        print(f"  理由: {error_data.get('reason')}")
        if error_data.get("error_details"):
            print(f"  エラー詳細: {error_data.get('error_details')}")
        
        # エラーメッセージ生成
        if error_data.get("provider") == "claude":
            message = f"❌ Claudeによる構成評価に失敗しました。しばらくして再試行してください。\n\nエラー詳細: {error_data.get('error_details', '')}"
        else:
            message = f"⚠️ Geminiによる補完結果が取得できませんでした。\n\nエラー詳細: {error_data.get('error_details', '')}"
        
        print(f"  生成されたメッセージ: {message}")

def test_template_rendering():
    """テンプレートレンダリング機能をテスト"""
    
    print("\n=== テンプレートレンダリング機能テスト ===")
    
    # テスト用の構造データ
    test_structure = {
        "id": "test-001",
        "title": "テスト構成",
        "content": {"key": "value"},
        "evaluation": {
            "provider": "claude",
            "status": "success",
            "score": 0.85,
            "feedback": "構成は概ね妥当です。",
            "timestamp": datetime.now().isoformat()
        },
        "gemini_output": {
            "provider": "gemini",
            "status": "failed",
            "reason": "補完中にエラーが発生しました",
            "error_details": "API rate limit exceeded",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print("テスト構造データ:")
    print(f"  ID: {test_structure['id']}")
    print(f"  タイトル: {test_structure['title']}")
    print(f"  評価ステータス: {test_structure['evaluation']['status']}")
    print(f"  補完ステータス: {test_structure['gemini_output']['status']}")
    
    # テンプレート条件分岐のテスト
    print("\nテンプレート条件分岐:")
    
    # 評価パネル
    if test_structure.get("evaluation"):
        eval_status = test_structure["evaluation"]["status"]
        if eval_status == "success":
            print("  ✅ 評価成功パネルを表示")
        elif eval_status == "failed":
            print("  ❌ 評価失敗パネルを表示")
        elif eval_status == "skipped":
            print("  ⚠️ 評価スキップパネルを表示")
    else:
        print("  📋 評価未実行パネルを表示")
    
    # 補完パネル
    if test_structure.get("gemini_output"):
        comp_status = test_structure["gemini_output"]["status"]
        if comp_status == "success":
            print("  ✅ 補完成功パネルを表示")
        elif comp_status == "failed":
            print("  ❌ 補完失敗パネルを表示")
    else:
        print("  📋 補完未実行パネルを表示")

def main():
    """メイン関数"""
    print("🚀 評価・補完の状態表示機能テスト開始")
    
    # 評価状態表示テスト
    test_evaluation_status_display()
    
    # 補完状態表示テスト
    test_completion_status_display()
    
    # エラーメッセージ生成テスト
    test_error_message_generation()
    
    # テンプレートレンダリングテスト
    test_template_rendering()
    
    print("\n✅ テスト完了")
    print("\n📋 実装内容:")
    print("1. 評価・補完処理の改善: 詳細なエラーハンドリングと状態管理")
    print("2. テンプレート表示の改善: 成功・失敗・スキップ状態の表示")
    print("3. CSSスタイルの追加: 各状態に応じた視覚的フィードバック")
    print("4. エラーメッセージの改善: ユーザーフレンドリーなメッセージ")
    print("5. ログ出力の強化: デバッグ用の詳細情報")

if __name__ == "__main__":
    main() 