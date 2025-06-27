#!/usr/bin/env python3
"""
Markdown抽出機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.files import extract_json_part, extract_structure_from_markdown

def test_markdown_extraction():
    """Markdown抽出機能をテスト"""
    
    # テストケース1: 基本的なMarkdown形式
    test_text_1 = """
# ブログサイト構成

## 説明
個人ブログサイトの基本構成です。

## ヘッダー
- ロゴ: サイトロゴ
- ナビゲーション: メニュー項目
- 検索機能: 検索ボックス

## メインコンテンツ
- 記事一覧: 最新記事の表示
- 記事詳細: 個別記事ページ
- カテゴリ: 記事分類

## サイドバー
- プロフィール: 著者情報
- カテゴリ一覧: カテゴリメニュー
- 最新記事: 最新記事リスト

## フッター
- コピーライト: 著作権表示
- リンク: 関連リンク
"""
    
    # テストケース2: 段落形式
    test_text_2 = """
# Eコマースサイト構成

## 説明
オンラインショッピングサイトの構成

## 商品ページ
商品の詳細情報を表示するページです。画像、価格、説明文を含みます。

## カート機能
購入したい商品を一時的に保存する機能です。数量変更や削除が可能です。

## 決済システム
クレジットカードや銀行振込などの決済方法を提供します。
"""
    
    print("=== Markdown抽出機能テスト ===")
    
    # テストケース1
    print("\n--- テストケース1: リスト形式 ---")
    result1 = extract_structure_from_markdown(test_text_1)
    if result1:
        print("✅ 抽出成功")
        print(f"タイトル: {result1.get('title')}")
        print(f"説明: {result1.get('description')}")
        print(f"セクション数: {len(result1.get('content', {}))}")
        for section_name, items in result1.get('content', {}).items():
            print(f"  {section_name}: {len(items)}個の項目")
    else:
        print("❌ 抽出失敗")
    
    # テストケース2
    print("\n--- テストケース2: 段落形式 ---")
    result2 = extract_structure_from_markdown(test_text_2)
    if result2:
        print("✅ 抽出成功")
        print(f"タイトル: {result2.get('title')}")
        print(f"説明: {result2.get('description')}")
        print(f"セクション数: {len(result2.get('content', {}))}")
        for section_name, items in result2.get('content', {}).items():
            print(f"  {section_name}: {len(items)}個の項目")
    else:
        print("❌ 抽出失敗")
    
    # extract_json_partでのテスト
    print("\n--- extract_json_partでのテスト ---")
    result3 = extract_json_part(test_text_1)
    if result3 and "error" not in result3:
        print("✅ extract_json_partでMarkdown抽出成功")
        print(f"タイトル: {result3.get('title')}")
        print(f"セクション数: {len(result3.get('content', {}))}")
    else:
        print("❌ extract_json_partでMarkdown抽出失敗")
        if "error" in result3:
            print(f"エラー: {result3['error']}")

if __name__ == "__main__":
    test_markdown_extraction() 