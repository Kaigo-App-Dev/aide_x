"""
Structure Feedback Engine

このモジュールは、ClaudeとGeminiの出力を比較し、JSONの構文エラーを修復する機能を提供します。
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
import difflib
from pathlib import Path
import re
from copy import deepcopy

logger = logging.getLogger(__name__)

class StructureFeedbackEngine:
    """構造フィードバックエンジン"""
    
    def __init__(self, log_dir: str = "logs/claude_gemini_diff"):
        """
        初期化
        
        Args:
            log_dir (str): 差分ログの保存ディレクトリ
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def fix_unquoted_keys(self, json_str: str) -> str:
        """
        未クオートのJSONキーを修正
        
        Args:
            json_str (str): 修正対象のJSON文字列
            
        Returns:
            str: 修正後のJSON文字列
        """
        # 文字列リテラル内のコロンを保護
        protected_str = re.sub(r'"[^"]*"', lambda m: m.group(0).replace(':', '\\u003A'), json_str)
        
        # 未クオートのキーを検出して修正
        # 1. オブジェクトの開始（{）またはカンマ（,）の後に続く
        # 2. 任意の空白文字
        # 3. 有効なキー名（英数字、アンダースコア、ハイフン）
        # 4. 任意の空白文字
        # 5. コロン（:）
        pattern = r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:'
        
        # キーをクオートで囲む
        fixed = re.sub(pattern, r'\1"\2":', protected_str)
        
        # 保護した文字列リテラルを元に戻す
        fixed = fixed.replace('\\u003A', ':')
        
        return fixed
    
    def repair_json(self, json_str: str, reference_json: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], bool]:
        """
        JSON文字列を修復
        
        Args:
            json_str (str): 修復対象のJSON文字列
            reference_json (Optional[Dict[str, Any]]): 参照用のJSON（Claude出力）
            
        Returns:
            Tuple[Dict[str, Any], bool]: (修復後のJSON, 修復が必要だったかどうか)
        """
        try:
            # まず通常のJSONパースを試行
            parsed_json = json.loads(json_str)
            if reference_json:
                # 参照JSONがある場合は、不足しているキーを補完
                return self.complement_missing_keys(parsed_json, reference_json), True
            return parsed_json, False
        except json.JSONDecodeError:
            # 未クオートキーの修正を試行
            fixed_json = self.fix_unquoted_keys(json_str)
            try:
                parsed_json = json.loads(fixed_json)
                if reference_json:
                    # 参照JSONがある場合は、不足しているキーを補完
                    return self.complement_missing_keys(parsed_json, reference_json), True
                return parsed_json, True
            except json.JSONDecodeError:
                if reference_json:
                    # パースに失敗した場合は、参照JSONの構造を使用
                    return deepcopy(reference_json), True
                raise
    
    def repair_with_reference(self, broken_json: str, reference_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        参照JSONを使用してJSONを修復
        
        Args:
            broken_json (str): 修復対象のJSON文字列
            reference_json (Dict[str, Any]): 参照用のJSON
            
        Returns:
            Dict[str, Any]: 修復後のJSON
        """
        # まず未クオートキーを修正
        fixed_json = self.fix_unquoted_keys(broken_json)
        try:
            # 修正後のJSONをパース
            parsed_json = json.loads(fixed_json)
            # 参照JSONと比較して不足しているキーを補完
            return self.complement_missing_keys(parsed_json, reference_json)
        except json.JSONDecodeError:
            # パースに失敗した場合は、参照JSONの構造を使用
            return deepcopy(reference_json)
    
    def complement_missing_keys(self, base: Dict[str, Any], reference: Dict[str, Any]) -> Dict[str, Any]:
        """
        不足しているキーを補完
        
        Args:
            base (Dict[str, Any]): 補完対象のJSON
            reference (Dict[str, Any]): 参照用のJSON
            
        Returns:
            Dict[str, Any]: 補完後のJSON
        """
        result = deepcopy(base)
        
        for key, value in reference.items():
            if key not in result:
                result[key] = deepcopy(value)
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self.complement_missing_keys(result[key], value)
            elif isinstance(value, list) and isinstance(result[key], list):
                result[key] = self._complement_list(result[key], value)
        
        return result
    
    def _complement_list(self, base_list: List[Any], reference_list: List[Any]) -> List[Any]:
        """
        リストの要素を補完
        
        Args:
            base_list (List[Any]): 補完対象のリスト
            reference_list (List[Any]): 参照用のリスト
            
        Returns:
            List[Any]: 補完後のリスト
        """
        result = deepcopy(base_list)
        
        for i, ref_item in enumerate(reference_list):
            if i >= len(result):
                result.append(deepcopy(ref_item))
            elif isinstance(ref_item, dict) and isinstance(result[i], dict):
                result[i] = self.complement_missing_keys(result[i], ref_item)
            elif isinstance(ref_item, list) and isinstance(result[i], list):
                result[i] = self._complement_list(result[i], ref_item)
        
        return result
    
    def save_diff_log(self, original: str, repaired: Dict[str, Any], reference: Optional[Dict[str, Any]] = None) -> str:
        """
        差分ログを保存
        
        Args:
            original (str): 元のJSON文字列
            repaired (Dict[str, Any]): 修復後のJSON
            reference (Optional[Dict[str, Any]]): 参照用のJSON
            
        Returns:
            str: ログファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"diff_{timestamp}.json")
        
        log_data = {
            "timestamp": timestamp,
            "original": original,
            "repaired": repaired,
            "reference": reference,
            "diff": self.generate_diff(original, json.dumps(repaired, indent=2))
        }
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        return log_file
    
    def generate_diff(self, original: str, repaired: str) -> str:
        """
        差分を生成
        
        Args:
            original (str): 元のテキスト
            repaired (str): 修復後のテキスト
            
        Returns:
            str: 差分テキスト
        """
        diff = difflib.unified_diff(
            original.splitlines(),
            repaired.splitlines(),
            lineterm=""
        )
        return "\n".join(diff)
    
    def process_structure(self, gemini_output: str, claude_output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        構造を処理
        
        Args:
            gemini_output (str): Geminiの出力
            claude_output (Optional[Dict[str, Any]]): Claudeの出力
            
        Returns:
            Dict[str, Any]: 処理後の構造
        """
        try:
            # JSONの修復を試行
            repaired_json, was_repaired = self.repair_json(gemini_output, claude_output)
            
            # 修復が必要だった場合はログを保存
            if was_repaired:
                self.save_diff_log(gemini_output, repaired_json, claude_output)
            
            return repaired_json
            
        except Exception as e:
            logger.error(f"Structure processing failed: {e}")
            if claude_output:
                # エラー時はClaudeの出力を信頼ソースとして使用
                return deepcopy(claude_output)
            raise 