"""
共通ユーティリティ関数
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
    テキストからJSON部分を抽出
    
    Args:
        text (str): JSONを含む可能性のあるテキスト
        
    Returns:
        Dict[str, Any]: 抽出されたJSONデータ
        
    Raises:
        ValueError: JSONの抽出に失敗した場合
    """
    # JSONオブジェクトを探す
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, text)
    
    if not match:
        raise ValueError("No JSON object found in text")
    
    json_str = match.group(0)
    
    # クォートされていないキーを修正
    json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        logger.error(f"JSON string: {json_str}")
        raise ValueError(f"Invalid JSON format: {e}")

def extract_json_part_old(text: str) -> Optional[Dict[str, Any]]:
    """
    Geminiの応答からJSON部分を抽出し、未クオートキーを修復
    
    Args:
        text: 抽出対象のテキスト
        
    Returns:
        Dict[str, Any]: 抽出・修復されたJSONオブジェクト
    """
    try:
        # JSON部分を抽出
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            logger.error("No JSON object found in text")
            return None
            
        json_str = json_match.group(0)
        
        # 未クオートキーを検出
        unquoted_keys = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*):', json_str)
        if unquoted_keys:
            logger.warning(f"Found unquoted keys: {unquoted_keys}")
            
            # エラーダンプを保存
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
            
            # 未クオートキーを修復
            for key in unquoted_keys:
                json_str = json_str.replace(f"{key}:", f'"{key}":')
        
        # JSONをパース
        return json.loads(json_str)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in extract_json_part: {str(e)}")
        return None 