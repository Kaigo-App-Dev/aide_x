"""
AIDE-X: ファイル操作・JSON抽出ユーティリティ
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

def extract_json_part(text: str) -> Dict[str, Any]:
    """
    テキストからJSON部分を抽出（改良版）
    Args:
        text (str): JSONを含む可能性のあるテキスト
    Returns:
        Dict[str, Any]: 抽出されたJSONデータ（失敗時はエラーメッセージを含む辞書）
    """
    if not text or not text.strip():
        logger.warning("extract_json_part: 空のテキストが提供されました")
        return {
            "error": "JSON構成が検出できませんでした",
            "reason": "空のテキストが提供されました",
            "original_text": ""
        }
    
    # テキストを前処理（Gemini出力対策）
    text = text.strip()
    
    # 半角スペースの正規化（複数のスペースを単一スペースに）
    text = re.sub(r'\s+', ' ', text)
    
    # 改行の正規化（改行を適切に処理）
    text = re.sub(r'\n\s*\n', '\n', text)  # 連続改行を単一改行に
    text = re.sub(r'\n\s*([{}])', r'\1', text)  # 波括弧前後の改行を削除
    
    logger.debug(f"extract_json_part: 入力テキスト長 = {len(text)}")
    logger.debug(f"extract_json_part: 入力テキスト内容 = {text[:500]}...")
    
    # 原文全文をlogs/に保存（Gemini出力分析用）
    try:
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/gemini_raw_output_{timestamp}.txt"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== Gemini Raw Output at {datetime.now().isoformat()} ===\n")
            f.write(f"Text Length: {len(text)}\n")
            f.write(f"Text Content:\n{text}\n")
            f.write("=" * 50 + "\n")
        logger.info(f"📝 Gemini原文を保存: {log_file}")
    except Exception as e:
        logger.warning(f"⚠️ Gemini原文保存に失敗: {e}")
    
    # 1. コードブロック（```json ... ```）を優先的に検索
    code_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    code_match = re.search(code_block_pattern, text)
    if code_match:
        json_str = code_match.group(1).strip()
        logger.debug(f"extract_json_part: コードブロックからJSONを抽出")
        try:
            result = json.loads(json_str)
            logger.debug(f"extract_json_part: コードブロックJSON抽出成功")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"コードブロックのJSONパース失敗: {e}")
            # コードブロックが失敗した場合、通常の抽出を試行
    
    # 2. 通常のJSONオブジェクトを検索
    json_pattern = r'\{[\s\S]*?\}'
    matches = list(re.finditer(json_pattern, text))
    
    if matches:
        # 複数のJSONオブジェクトが見つかった場合、最も長いものを選択
        longest_match = max(matches, key=lambda m: len(m.group(0)))
        json_str = longest_match.group(0)
        logger.debug(f"extract_json_part: 抽出されたJSON文字列長 = {len(json_str)}")
        
        # 3. 未クオートキーの修復
        # パターン: {key: value} -> {"key": value}
        json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
        
        # 4. 末尾のカンマを削除
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 5. 複数回パースを試行（段階的に修復）
        for attempt in range(3):
            try:
                result = json.loads(json_str)
                logger.debug(f"extract_json_part: JSON抽出成功 (試行{attempt + 1})")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"extract_json_part: JSONパース失敗 (試行{attempt + 1}): {e}")
                if attempt < 2:  # 最後の試行でない場合
                    # 追加の修復を試行
                    if "True" in json_str:
                        json_str = json_str.replace("True", "true")
                    if "False" in json_str:
                        json_str = json_str.replace("False", "false")
                    if "None" in json_str:
                        json_str = json_str.replace("None", "null")
                    
                    # 特殊文字のエスケープ処理
                    json_str = re.sub(r'([^\\])"', r'\1\\"', json_str)
                    json_str = json_str.replace('\\"', '"')  # 二重エスケープを修正
                else:
                    logger.error(f"extract_json_part: 最終JSONパース失敗: {e}")
                    logger.error(f"extract_json_part: 処理後のJSON文字列 = {json_str}")
                    
                    # パース失敗時もエラー情報を含む辞書を返す
                    return {
                        "error": "JSON構成の解析に失敗しました",
                        "reason": f"JSONパースエラー: {str(e)}",
                        "extracted_json_string": json_str,
                        "original_text": text[:200] + "..." if len(text) > 200 else text
                    }
    
    # 6. JSONが見つからない場合、Markdown形式から構成情報を抽出
    logger.info("🔍 JSONが見つからないため、Markdown形式から構成情報を抽出を試行")
    extracted_structure = extract_structure_from_markdown(text)
    if extracted_structure:
        logger.info("✅ Markdown形式から構成情報を抽出成功")
        return extracted_structure
    
    # 7. 最終的にエラー情報を返す
    logger.error(f"extract_json_part: JSONオブジェクトが見つかりません")
    logger.error(f"extract_json_part: 入力テキスト全文 = {text}")
    logger.error(f"extract_json_part: テキスト長 = {len(text)}")
    logger.error(f"extract_json_part: テキストの最初の100文字 = {text[:100]}")
    logger.error(f"extract_json_part: テキストの最後の100文字 = {text[-100:]}")
    
    # テキストの特徴を分析
    if "```" in text:
        logger.error(f"extract_json_part: コードブロックは存在するが、JSONが見つからない")
    if "{" in text and "}" in text:
        logger.error(f"extract_json_part: 波括弧は存在するが、有効なJSONオブジェクトではない")
    if "[" in text and "]" in text:
        logger.error(f"extract_json_part: 角括弧（配列）は存在するが、オブジェクトではない")
    
    # エラー情報を含む辞書を返す
    return {
        "error": "JSON構成が検出できませんでした",
        "reason": "テキストに有効なJSONオブジェクトが含まれていません",
        "original_text": text[:200] + "..." if len(text) > 200 else text,
        "text_length": len(text)
    }

def extract_structure_from_markdown(text: str) -> Optional[Dict[str, Any]]:
    """
    Markdown形式のテキストから構成情報を抽出する
    
    Args:
        text (str): Markdown形式のテキスト
        
    Returns:
        Optional[Dict[str, Any]]: 抽出された構成情報、失敗時はNone
    """
    try:
        logger.debug("🔍 Markdown形式からの構成抽出開始")
        
        # タイトルを抽出（# で始まる行）
        title_match = re.search(r'^#\s*(.+)$', text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "自動生成された構成"
        
        # 説明を抽出（## 説明 または 説明: で始まる行）
        description_match = re.search(r'(?:^##\s*説明\s*$|^説明\s*:?\s*$)(.+?)(?=^##|\Z)', text, re.MULTILINE | re.DOTALL)
        description = description_match.group(1).strip() if description_match else ""
        
        # セクションを抽出（## で始まる行）
        sections = {}
        section_pattern = r'^##\s*(.+?)$\s*((?:(?!^##).)*?)(?=^##|\Z)'
        section_matches = re.finditer(section_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in section_matches:
            section_name = match.group(1).strip()
            section_content = match.group(2).strip()
            
            # セクション内容から項目を抽出
            items = {}
            
            # リスト項目を抽出（- または * で始まる行）
            list_items = re.findall(r'^[-*]\s*(.+?)$', section_content, re.MULTILINE)
            if list_items:
                for i, item in enumerate(list_items):
                    items[f"item_{i+1}"] = item.strip()
            else:
                # リストがない場合は段落を項目として扱う
                paragraphs = [p.strip() for p in section_content.split('\n\n') if p.strip()]
                for i, paragraph in enumerate(paragraphs):
                    if paragraph and not paragraph.startswith('#'):
                        items[f"paragraph_{i+1}"] = paragraph
            
            if items:
                sections[section_name] = items
        
        # 構成情報を構築
        if sections:
            structure = {
                "title": title,
                "description": description,
                "content": sections
            }
            logger.debug(f"✅ Markdown構成抽出成功: {len(sections)}個のセクション")
            return structure
        else:
            logger.warning("⚠️ Markdown形式からセクションを抽出できませんでした")
            return None
            
    except Exception as e:
        logger.error(f"❌ Markdown形式からの構成抽出エラー: {e}")
        return None

def extract_json_part_old(text: str) -> Optional[Dict[str, Any]]:
    """
    Geminiの応答からJSON部分を抽出し、未クオートキーを修復
    Args:
        text: 抽出対象のテキスト
    Returns:
        Dict[str, Any]: 抽出・修復されたJSONオブジェクト
    """
    try:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            logger.error("No JSON object found in text")
            return None
        json_str = json_match.group(0)
        unquoted_keys = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\:', json_str)
        if unquoted_keys:
            logger.warning(f"Found unquoted keys: {unquoted_keys}")
            dump_dir = "logs"
            if not os.path.exists(dump_dir):
                os.makedirs(dump_dir)
            timestamp = datetime.now().strftime("%Y%m%d")
            dump_file = os.path.join(dump_dir, f"gemini_error_dump_{timestamp}.json")
            with open(dump_file, "a", encoding="utf-8") as f:
                f.write(f"\n=== Error at {datetime.now()} ===\n")
                f.write(f"Original text: {text}\n")
                f.write(f"Extracted JSON: {json_str}\n")
                f.write(f"Unquoted keys: {unquoted_keys}\n")
            for key in unquoted_keys:
                json_str = json_str.replace(f"{key}:", f'"{key}":')
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in extract_json_part: {str(e)}")
        return None 