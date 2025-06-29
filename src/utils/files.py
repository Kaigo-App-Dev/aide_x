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
    ChatGPT応答からJSON構成部分を抽出する関数
    
    Args:
        text (str): ChatGPT応答のテキスト
        
    Returns:
        Dict[str, Any]: 抽出されたJSONデータまたはエラー情報
    """
    logger.info(f"🔍 extract_json_part: 入力テキスト長 = {len(text)}")
    
    # 入力テキストの保存（デバッグ用）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/chatgpt_raw_output_{timestamp}.txt"
    try:
        os.makedirs("logs", exist_ok=True)
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"📝 ChatGPT原文を保存: {log_filename}")
    except Exception as e:
        logger.warning(f"ChatGPT原文の保存に失敗: {e}")
    
    # 1. コードブロック内のJSONを検索（最優先）
    code_block_pattern = r'```(?:json)?\s*\n([\s\S]*?)\n```'
    code_matches = re.findall(code_block_pattern, text)
    
    for json_str in code_matches:
        json_str = json_str.strip()
        if json_str.startswith('{') and json_str.endswith('}'):
            logger.info("🔍 extract_json_part: コードブロックからJSONを抽出")
            
            # 未クオートキーの検出と修復
            json_str = repair_unquoted_keys(json_str)
            
            # JSONバリデーション
            validation_result = validate_json_string(json_str)
            if validation_result["is_valid"]:
                logger.info("✅ extract_json_part: コードブロックJSON抽出成功")
                return validation_result["data"]
            else:
                logger.warning(f"コードブロックのJSONバリデーション失敗: {validation_result['error']}")
                # 次のコードブロックを試行
    
    # 2. 完全なJSONオブジェクトを検索（括弧の均衡を考慮）
    # より正確なJSON抽出パターン
    def find_complete_json(text: str) -> Optional[str]:
        """完全なJSONオブジェクトを検索する関数"""
        start = 0
        while True:
            # 開き括弧を探す
            open_pos = text.find('{', start)
            if open_pos == -1:
                break
            
            # その位置から完全なJSONオブジェクトを構築
            brace_count = 0
            pos = open_pos
            in_string = False
            escape_next = False
            
            while pos < len(text):
                char = text[pos]
                
                if escape_next:
                    escape_next = False
                elif char == '\\':
                    escape_next = True
                elif char == '"' and not escape_next:
                    in_string = not in_string
                elif not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # 完全なJSONオブジェクトが見つかった
                            json_str = text[open_pos:pos + 1]
                            # 基本的な検証
                            if len(json_str) > 10:  # 最小サイズチェック
                                return json_str
                            break
                
                pos += 1
            
            start = open_pos + 1
        
        return None
    
    # 完全なJSONオブジェクトを検索
    complete_json = find_complete_json(text)
    if complete_json:
        logger.info(f"🔍 extract_json_part: 完全なJSONオブジェクトを検出（長さ: {len(complete_json)}）")
        
        # 未クオートキーの検出と修復
        complete_json = repair_unquoted_keys(complete_json)
        
        # 末尾のカンマを削除
        complete_json = re.sub(r',(\s*[}\]])', r'\1', complete_json)
        
        # JSONバリデーション
        validation_result = validate_json_string(complete_json)
        if validation_result["is_valid"]:
            logger.info("✅ extract_json_part: 完全なJSONオブジェクト抽出成功")
            return validation_result["data"]
        else:
            logger.error(f"❌ extract_json_part: 完全なJSONオブジェクトのバリデーション失敗: {validation_result['error']}")
            logger.error(f"❌ extract_json_part: 処理後のJSON文字列 = {complete_json}")
            logger.error(f"❌ extract_json_part: エラー位置の詳細分析:")
            
            # エラー位置の詳細分析
            try:
                json.loads(complete_json)
            except json.JSONDecodeError as json_error:
                logger.error(f"❌ JSONDecodeError詳細:")
                logger.error(f"   - エラーメッセージ: {json_error.msg}")
                logger.error(f"   - エラー位置: 行{json_error.lineno}, 列{json_error.colno}")
                logger.error(f"   - エラー行の内容: {json_error.doc.split(chr(10))[json_error.lineno-1] if json_error.lineno > 0 else 'N/A'}")
                logger.error(f"   - エラー位置の文字: '{json_error.doc[json_error.pos] if json_error.pos < len(json_error.doc) else 'N/A'}'")
            
            return {
                "error": "JSON構成の解析に失敗しました",
                "reason": f"JSONバリデーションエラー: {validation_result['error']}",
                "extracted_json_string": complete_json,
                "original_text": text[:200] + "..." if len(text) > 200 else text
            }
    
    # 3. ChatGPT応答特有のパターンを検索
    chatgpt_patterns = [
        r'構成[：:]\s*(\{[\s\S]*?\})',  # 「構成: {JSON}」形式
        r'JSON[：:]\s*(\{[\s\S]*?\})',  # 「JSON: {JSON}」形式
        r'構造[：:]\s*(\{[\s\S]*?\})',  # 「構造: {JSON}」形式
        r'以下の構成[：:]\s*(\{[\s\S]*?\})',  # 「以下の構成: {JSON}」形式
    ]
    
    for pattern in chatgpt_patterns:
        match = re.search(pattern, text)
        if match:
            json_str = match.group(1).strip()
            logger.info(f"🔍 extract_json_part: ChatGPT特有パターンからJSONを抽出（パターン: {pattern[:20]}...）")
            
            # 未クオートキーの検出と修復
            json_str = repair_unquoted_keys(json_str)
            
            # JSONバリデーション
            validation_result = validate_json_string(json_str)
            if validation_result["is_valid"]:
                logger.info(f"✅ extract_json_part: ChatGPT特有パターンJSON抽出成功")
                return validation_result["data"]
            else:
                logger.warning(f"ChatGPT特有パターンのJSONバリデーション失敗: {validation_result['error']}")
                # 次のパターンを試行
    
    # 4. JSONが見つからない場合、Markdown形式から構成情報を抽出
    logger.info("🔍 JSONが見つからないため、Markdown形式から構成情報を抽出を試行")
    extracted_structure = extract_structure_from_markdown(text)
    if extracted_structure:
        logger.info("✅ Markdown形式から構成情報を抽出成功")
        return extracted_structure
    
    # 5. 最終的にエラー情報を返す（詳細なログ出力）
    logger.error(f"❌ extract_json_part: JSONオブジェクトが見つかりません")
    logger.error(f"extract_json_part: 入力テキスト全文 = {text}")
    logger.error(f"extract_json_part: テキスト長 = {len(text)}")
    logger.error(f"extract_json_part: テキストの最初の200文字 = {text[:200]}")
    logger.error(f"extract_json_part: テキストの最後の200文字 = {text[-200:]}")
    
    # テキストの特徴を分析
    if "```" in text:
        logger.error(f"extract_json_part: コードブロックは存在するが、JSONが見つからない")
    if "{" in text and "}" in text:
        logger.error(f"extract_json_part: 波括弧は存在するが、有効なJSONオブジェクトではない")
    if "[" in text and "]" in text:
        logger.error(f"extract_json_part: 角括弧（配列）は存在するが、オブジェクトではない")
    
    # ChatGPT応答特有のキーワードチェック
    chatgpt_keywords = ["構成", "JSON", "構造", "モジュール", "機能"]
    found_keywords = [kw for kw in chatgpt_keywords if kw in text]
    if found_keywords:
        logger.error(f"extract_json_part: ChatGPT応答らしいキーワードを検出: {found_keywords}")
    
    # エラー情報を含む辞書を返す
    return {
        "error": "JSON構成が検出できませんでした",
        "reason": "テキストに有効なJSONオブジェクトが含まれていません",
        "original_text": text[:200] + "..." if len(text) > 200 else text,
        "text_length": len(text),
        "found_keywords": found_keywords if 'found_keywords' in locals() else []
    }

def validate_json_string(json_str: str) -> Dict[str, Any]:
    """
    JSON文字列のバリデーションを実行
    
    Args:
        json_str (str): バリデーション対象のJSON文字列
        
    Returns:
        Dict[str, Any]: バリデーション結果
            - is_valid (bool): バリデーション成功フラグ
            - data (Dict[str, Any]): パースされたJSONデータ（成功時）
            - error (str): エラーメッセージ（失敗時）
    """
    if not json_str or not json_str.strip():
        return {
            "is_valid": False,
            "error": "空のJSON文字列が提供されました"
        }
    
    # 基本的な構文チェック
    json_str = json_str.strip()
    
    # 不完全なJSONの検出
    if json_str == "{" or json_str == "}":
        return {
            "is_valid": False,
            "error": f"不完全なJSON: '{json_str}'"
        }
    
    if json_str.startswith("{") and not json_str.endswith("}"):
        return {
            "is_valid": False,
            "error": f"不完全なJSON: 開き括弧のみ '{json_str[:50]}...'"
        }
    
    if not json_str.startswith("{") and json_str.endswith("}"):
        return {
            "is_valid": False,
            "error": f"不完全なJSON: 閉じ括弧のみ '...{json_str[-50:]}'"
        }
    
    # 括弧の均衡チェック
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    if open_braces != close_braces:
        return {
            "is_valid": False,
            "error": f"括弧の不均衡: 開き括弧{open_braces}個、閉じ括弧{close_braces}個"
        }
    
    # 複数回パースを試行（段階的に修復）
    for attempt in range(3):
        try:
            result = json.loads(json_str)
            return {
                "is_valid": True,
                "data": result
            }
        except json.JSONDecodeError as e:
            logger.warning(f"validate_json_string: JSONパース失敗 (試行{attempt + 1}): {e}")
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
                return {
                    "is_valid": False,
                    "error": f"JSONパースエラー: {str(e)}"
                }
    
    return {
        "is_valid": False,
        "error": "予期しないエラーが発生しました"
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

def repair_unquoted_keys(json_str: str) -> str:
    """
    未クオートキーを修復する
    
    Args:
        json_str (str): 修復対象のJSON文字列
        
    Returns:
        str: 修復されたJSON文字列
    """
    # 未クオートキーの検出（複数のパターンに対応）
    # パターン1: 通常の未クオートキー (title:)
    unquoted_keys = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', json_str)
    
    # パターン2: 日本語文字を含む未クオートキー (「title」:)
    japanese_unquoted_keys = re.findall(r'([「」\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+)\s*:', json_str)
    
    # パターン3: 特殊文字を含む未クオートキー
    special_unquoted_keys = re.findall(r'([^\s:,\{\}\[\]"]+)\s*:', json_str)
    
    all_unquoted_keys = unquoted_keys + japanese_unquoted_keys + special_unquoted_keys
    all_unquoted_keys = list(set(all_unquoted_keys))  # 重複を除去
    
    if all_unquoted_keys:
        logger.warning(f"未クオートキーを検出: {all_unquoted_keys}")
        
        # 未クオートキーをクオートで囲む
        for key in all_unquoted_keys:
            # 既にクオートされている場合はスキップ
            if f'"{key}":' in json_str:
                continue
            
            # 特殊文字を含むキーの場合は適切にエスケープ
            escaped_key = key.replace('"', '\\"').replace('\\', '\\\\')
            
            # 未クオートキーをクオートで囲む（複数のパターンに対応）
            # パターン1: {key: または ,key:
            json_str = re.sub(rf'([{{,])\s*{re.escape(key)}\s*:', rf'\1"{escaped_key}":', json_str)
            
            # パターン2: 行頭のkey:
            json_str = re.sub(rf'^\s*{re.escape(key)}\s*:', rf'"{escaped_key}":', json_str, flags=re.MULTILINE)
        
        logger.info(f"未クオートキーの修復完了: {len(all_unquoted_keys)}個")
    
    return json_str

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