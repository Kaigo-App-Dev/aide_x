"""
構成分析モジュール
構造JSONの完成度・状態を分析する機能を提供
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def analyze_structure_state(structure: Optional[dict]) -> dict:
    """
    構成JSONの完成度・状態を分析する
    
    Args:
        structure: 分析対象の構成辞書
        
    Returns:
        分析結果を含む辞書:
        {
            "is_empty": bool,               # 構成が空かどうか
            "module_count": int,           # モジュール数
            "incomplete_modules": list,    # 未記入フィールドを含むモジュール
            "missing_fields": list,        # 構成全体で不足しているキー
            "diagnostic_message": str,     # 診断結果メッセージ
        }
    """
    logger.debug(f"構成分析開始: structure keys = {list(structure.keys()) if structure else 'None'}")
    
    # 初期化
    result = {
        "is_empty": False,
        "module_count": 0,
        "incomplete_modules": [],
        "missing_fields": [],
        "diagnostic_message": ""
    }
    
    # 空チェック
    if not structure:
        result["is_empty"] = True
        result["diagnostic_message"] = "構成が空です"
        logger.debug("構成が空と判定")
        return result
    
    # modulesの存在チェック
    modules = structure.get("modules")
    if not modules:
        result["is_empty"] = True
        result["diagnostic_message"] = "モジュールが定義されていません"
        logger.debug("モジュールが存在しないと判定")
        return result
    
    # modulesがリストかチェック
    if not isinstance(modules, list):
        result["is_empty"] = True
        result["diagnostic_message"] = "モジュールがリスト形式ではありません"
        logger.debug(f"モジュールがリストではない: {type(modules)}")
        return result
    
    # モジュール数
    result["module_count"] = len(modules)
    logger.debug(f"モジュール数: {result['module_count']}")
    
    # 空のモジュールリストの場合
    if result["module_count"] == 0:
        result["is_empty"] = True
        result["diagnostic_message"] = "モジュールが定義されていません"
        logger.debug("モジュールリストが空と判定")
        return result
    
    # 必須フィールドの定義
    required_fields = ["title", "description"]
    optional_fields = ["type", "id", "dependencies", "config"]
    
    # 全体で出現しているフィールドを収集
    all_fields = set()
    incomplete_modules = []
    
    # 各モジュールを分析
    for i, module in enumerate(modules):
        if not isinstance(module, dict):
            logger.warning(f"モジュール {i} が辞書ではありません: {type(module)}")
            incomplete_modules.append({
                "index": i,
                "name": f"モジュール{i}",
                "reason": "辞書形式ではありません"
            })
            continue
        
        # フィールドを収集
        module_fields = set(module.keys())
        all_fields.update(module_fields)
        
        # 必須フィールドのチェック
        missing_required = []
        for field in required_fields:
            if field not in module or not module[field]:
                missing_required.append(field)
        
        if missing_required:
            module_name = module.get("title", f"モジュール{i}")
            incomplete_modules.append({
                "index": i,
                "name": module_name,
                "missing_fields": missing_required,
                "reason": f"必須フィールドが不足: {', '.join(missing_required)}"
            })
            logger.debug(f"モジュール {i} ({module_name}) に不足フィールド: {missing_required}")
    
    result["incomplete_modules"] = incomplete_modules
    
    # 全体で不足しているフィールドを判定
    missing_fields = []
    for field in required_fields:
        if field not in all_fields:
            missing_fields.append(field)
    
    result["missing_fields"] = missing_fields
    
    # 診断メッセージを生成
    result["diagnostic_message"] = generate_diagnostic_message(result)
    
    logger.debug(f"構成分析完了: {result['diagnostic_message']}")
    return result


def generate_diagnostic_message(analysis_result: dict) -> str:
    """
    分析結果から診断メッセージを生成
    
    Args:
        analysis_result: analyze_structure_state()の結果
        
    Returns:
        診断メッセージ
    """
    if analysis_result["is_empty"]:
        return analysis_result["diagnostic_message"]
    
    module_count = analysis_result["module_count"]
    incomplete_count = len(analysis_result["incomplete_modules"])
    missing_fields = analysis_result["missing_fields"]
    
    messages = []
    
    # モジュール数
    if module_count == 0:
        messages.append("モジュールが定義されていません")
    elif module_count == 1:
        messages.append("1個のモジュールが定義されています")
    else:
        messages.append(f"{module_count}個のモジュールが定義されています")
    
    # 不完全なモジュール
    if incomplete_count > 0:
        if incomplete_count == 1:
            messages.append("1個のモジュールに記述漏れがあります")
        else:
            messages.append(f"{incomplete_count}個のモジュールに記述漏れがあります")
    
    # 不足フィールド
    if missing_fields:
        fields_str = ", ".join(missing_fields)
        messages.append(f"{fields_str} が不足しています")
    
    # 完全な場合
    if incomplete_count == 0 and not missing_fields and module_count > 0:
        messages.append("構成は完成しています")
    
    return "。".join(messages) + "。"


def get_structure_completion_rate(structure: dict) -> float:
    """
    構成の完成度を0.0-1.0の範囲で返す
    
    Args:
        structure: 分析対象の構成辞書
        
    Returns:
        完成度（0.0-1.0）
    """
    analysis = analyze_structure_state(structure)
    
    if analysis["is_empty"]:
        return 0.0
    
    module_count = analysis["module_count"]
    if module_count == 0:
        return 0.0
    
    # 不完全なモジュールの割合を計算
    incomplete_count = len(analysis["incomplete_modules"])
    completion_rate = (module_count - incomplete_count) / module_count
    
    return round(completion_rate, 2)


def get_structure_quality_score(structure: dict) -> dict:
    """
    構成の品質スコアを計算
    
    Args:
        structure: 分析対象の構成辞書
        
    Returns:
        品質スコア情報:
        {
            "completion_rate": float,    # 完成度（0.0-1.0）
            "quality_score": float,      # 品質スコア（0.0-1.0）
            "missing_required_fields": int,  # 不足必須フィールド数
            "total_modules": int,        # 総モジュール数
            "complete_modules": int,     # 完成モジュール数
        }
    """
    analysis = analyze_structure_state(structure)
    
    if analysis["is_empty"]:
        return {
            "completion_rate": 0.0,
            "quality_score": 0.0,
            "missing_required_fields": 0,
            "total_modules": 0,
            "complete_modules": 0
        }
    
    module_count = analysis["module_count"]
    incomplete_count = len(analysis["incomplete_modules"])
    complete_count = module_count - incomplete_count
    
    # 完成度
    completion_rate = complete_count / module_count if module_count > 0 else 0.0
    
    # 品質スコア（完成度 + フィールドの充実度）
    field_penalty = len(analysis["missing_fields"]) * 0.1
    quality_score = max(0.0, completion_rate - field_penalty)
    
    return {
        "completion_rate": round(completion_rate, 2),
        "quality_score": round(quality_score, 2),
        "missing_required_fields": len(analysis["missing_fields"]),
        "total_modules": module_count,
        "complete_modules": complete_count
    } 