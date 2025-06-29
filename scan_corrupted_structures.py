#!/usr/bin/env python3
"""
壊れた構成データの一括洗い出しスクリプト
structure["structure"] または structure["gemini_output"] に格納された
不正なJSONデータを検出・報告する
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.files import validate_json_string
from src.structure.utils import load_structure_by_id

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'corrupted_structures_scan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )
    return logging.getLogger(__name__)

def get_data_directory() -> str:
    """データディレクトリを取得"""
    # 環境変数から取得を試行
    data_dir = os.getenv('AIDEX_DATA_DIR', 'data')
    return data_dir

def scan_structure_files() -> List[str]:
    """構造ファイルの一覧を取得"""
    logger = setup_logging()
    data_dir = get_data_directory()
    structure_files = []
    
    # 複数の候補パスを確認
    possible_paths = [
        os.path.join(data_dir, "default"),
        data_dir,
        "structures",
        "data"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"📂 スキャン対象ディレクトリ: {path}")
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.json') and not file.endswith('_history.json'):
                        file_path = os.path.join(root, file)
                        structure_id = file.replace('.json', '')
                        structure_files.append((structure_id, file_path))
    
    logger.info(f"📋 発見された構造ファイル数: {len(structure_files)}")
    return structure_files

def analyze_structure_data(structure_id: str, file_path: str) -> Dict[str, Any]:
    """構造データを分析"""
    logger = setup_logging()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        
        analysis = {
            "structure_id": structure_id,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "structure_field_analysis": None,
            "gemini_output_analysis": None,
            "overall_status": "unknown"
        }
        
        # structure["structure"]の分析
        if "structure" in structure:
            structure_data = structure["structure"]
            analysis["structure_field_analysis"] = analyze_json_field(
                "structure", structure_data, structure_id
            )
        
        # structure["gemini_output"]の分析
        if "gemini_output" in structure:
            gemini_output = structure["gemini_output"]
            analysis["gemini_output_analysis"] = analyze_gemini_output(
                gemini_output, structure_id
            )
        
        # 全体ステータスの判定
        structure_status = analysis["structure_field_analysis"]["status"] if analysis["structure_field_analysis"] else "not_found"
        gemini_status = analysis["gemini_output_analysis"]["status"] if analysis["gemini_output_analysis"] else "not_found"
        
        if structure_status == "corrupted" or gemini_status == "corrupted":
            analysis["overall_status"] = "corrupted"
        elif structure_status == "valid" or gemini_status == "valid":
            analysis["overall_status"] = "valid"
        else:
            analysis["overall_status"] = "unknown"
        
        return analysis
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSONデコードエラー: {file_path} - {e}")
        return {
            "structure_id": structure_id,
            "file_path": file_path,
            "error": f"JSONデコードエラー: {str(e)}",
            "overall_status": "corrupted"
        }
    except Exception as e:
        logger.error(f"❌ ファイル読み込みエラー: {file_path} - {e}")
        return {
            "structure_id": structure_id,
            "file_path": file_path,
            "error": f"ファイル読み込みエラー: {str(e)}",
            "overall_status": "error"
        }

def analyze_json_field(field_name: str, field_data: Any, structure_id: str) -> Dict[str, Any]:
    """JSONフィールドの分析"""
    analysis = {
        "field_name": field_name,
        "data_type": type(field_data).__name__,
        "status": "unknown",
        "error_details": None,
        "data_preview": None
    }
    
    if field_data is None:
        analysis["status"] = "null"
        return analysis
    
    if isinstance(field_data, str):
        analysis["data_preview"] = field_data[:100] + "..." if len(field_data) > 100 else field_data
        
        # 不完全なJSONの検出
        field_data_trimmed = field_data.strip()
        if field_data_trimmed == "{":
            analysis["status"] = "corrupted"
            analysis["error_details"] = "不完全なJSON: 開き括弧のみ"
            return analysis
        
        if field_data_trimmed == "}":
            analysis["status"] = "corrupted"
            analysis["error_details"] = "不完全なJSON: 閉じ括弧のみ"
            return analysis
        
        if field_data_trimmed.startswith("{") and not field_data_trimmed.endswith("}"):
            analysis["status"] = "corrupted"
            analysis["error_details"] = "不完全なJSON: 開き括弧のみ（長い文字列）"
            return analysis
        
        if not field_data_trimmed.startswith("{") and field_data_trimmed.endswith("}"):
            analysis["status"] = "corrupted"
            analysis["error_details"] = "不完全なJSON: 閉じ括弧のみ（長い文字列）"
            return analysis
        
        # 括弧の均衡チェック
        open_braces = field_data_trimmed.count('{')
        close_braces = field_data_trimmed.count('}')
        if open_braces != close_braces:
            analysis["status"] = "corrupted"
            analysis["error_details"] = f"括弧の不均衡: 開き括弧{open_braces}個、閉じ括弧{close_braces}個"
            return analysis
        
        # 未クオートキーの検出
        unquoted_keys = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', field_data_trimmed)
        if unquoted_keys:
            analysis["status"] = "corrupted"
            analysis["error_details"] = f"未クオートキー: {unquoted_keys}"
            return analysis
        
        # JSONバリデーション
        validation_result = validate_json_string(field_data_trimmed)
        if validation_result["is_valid"]:
            analysis["status"] = "valid"
        else:
            analysis["status"] = "corrupted"
            analysis["error_details"] = validation_result["error"]
    
    elif isinstance(field_data, dict):
        analysis["status"] = "valid"
        analysis["data_preview"] = f"オブジェクト（{len(field_data)}個のキー）"
    
    elif isinstance(field_data, list):
        analysis["status"] = "valid"
        analysis["data_preview"] = f"配列（{len(field_data)}個の要素）"
    
    else:
        analysis["status"] = "unknown"
        analysis["error_details"] = f"予期しないデータ型: {type(field_data)}"
    
    return analysis

def analyze_gemini_output(gemini_output: Any, structure_id: str) -> Dict[str, Any]:
    """gemini_outputフィールドの分析"""
    analysis = {
        "field_name": "gemini_output",
        "data_type": type(gemini_output).__name__,
        "status": "unknown",
        "error_details": None,
        "content_analysis": None
    }
    
    if gemini_output is None:
        analysis["status"] = "null"
        return analysis
    
    if isinstance(gemini_output, dict):
        # contentフィールドの分析
        if "content" in gemini_output:
            content_analysis = analyze_json_field("content", gemini_output["content"], structure_id)
            analysis["content_analysis"] = content_analysis
            
            if content_analysis["status"] == "corrupted":
                analysis["status"] = "corrupted"
                analysis["error_details"] = f"contentフィールドが破損: {content_analysis['error_details']}"
            elif content_analysis["status"] == "valid":
                analysis["status"] = "valid"
            else:
                analysis["status"] = content_analysis["status"]
        
        # extracted_jsonフィールドの分析
        elif "extracted_json" in gemini_output:
            extracted_analysis = analyze_json_field("extracted_json", gemini_output["extracted_json"], structure_id)
            analysis["content_analysis"] = extracted_analysis
            
            if extracted_analysis["status"] == "corrupted":
                analysis["status"] = "corrupted"
                analysis["error_details"] = f"extracted_jsonフィールドが破損: {extracted_analysis['error_details']}"
            elif extracted_analysis["status"] == "valid":
                analysis["status"] = "valid"
            else:
                analysis["status"] = extracted_analysis["status"]
        
        else:
            analysis["status"] = "unknown"
            analysis["error_details"] = "contentまたはextracted_jsonフィールドが見つかりません"
    
    else:
        analysis["status"] = "unknown"
        analysis["error_details"] = f"予期しないデータ型: {type(gemini_output)}"
    
    return analysis

def generate_report(analyses: List[Dict[str, Any]]) -> str:
    """分析結果のレポートを生成"""
    total_count = len(analyses)
    corrupted_count = sum(1 for a in analyses if a.get("overall_status") == "corrupted")
    valid_count = sum(1 for a in analyses if a.get("overall_status") == "valid")
    error_count = sum(1 for a in analyses if a.get("overall_status") == "error")
    unknown_count = total_count - corrupted_count - valid_count - error_count
    
    report = f"""
# 壊れた構成データ スキャンレポート
生成日時: {datetime.now().isoformat()}

## 概要
- 総ファイル数: {total_count}
- 破損ファイル数: {corrupted_count}
- 正常ファイル数: {valid_count}
- エラーファイル数: {error_count}
- 不明ファイル数: {unknown_count}

## 破損ファイル詳細
"""
    
    corrupted_files = [a for a in analyses if a.get("overall_status") == "corrupted"]
    for analysis in corrupted_files:
        report += f"""
### {analysis['structure_id']}
- ファイルパス: {analysis['file_path']}
- ファイルサイズ: {analysis.get('file_size', 'N/A')} bytes
- 最終更新: {analysis.get('modified_time', 'N/A')}

"""
        
        if analysis.get("structure_field_analysis"):
            sa = analysis["structure_field_analysis"]
            report += f"- structureフィールド: {sa['status']}"
            if sa.get("error_details"):
                report += f" - {sa['error_details']}"
            report += "\n"
        
        if analysis.get("gemini_output_analysis"):
            ga = analysis["gemini_output_analysis"]
            report += f"- gemini_outputフィールド: {ga['status']}"
            if ga.get("error_details"):
                report += f" - {ga['error_details']}"
            report += "\n"
    
    # 破損ファイルの一覧（CSV形式）
    report += f"""
## 破損ファイル一覧（CSV形式）
structure_id,file_path,file_size,modified_time,structure_status,gemini_output_status,error_details
"""
    
    for analysis in corrupted_files:
        structure_status = analysis.get("structure_field_analysis", {}).get("status", "not_found")
        gemini_status = analysis.get("gemini_output_analysis", {}).get("status", "not_found")
        error_details = ""
        
        if analysis.get("structure_field_analysis", {}).get("error_details"):
            error_details += f"structure: {analysis['structure_field_analysis']['error_details']}; "
        if analysis.get("gemini_output_analysis", {}).get("error_details"):
            error_details += f"gemini_output: {analysis['gemini_output_analysis']['error_details']}"
        
        report += f"{analysis['structure_id']},{analysis['file_path']},{analysis.get('file_size', 'N/A')},{analysis.get('modified_time', 'N/A')},{structure_status},{gemini_status},\"{error_details}\"\n"
    
    return report

def main():
    """メイン関数"""
    logger = setup_logging()
    logger.info("🚀 壊れた構成データのスキャンを開始")
    
    # 構造ファイルの一覧を取得
    structure_files = scan_structure_files()
    
    if not structure_files:
        logger.warning("⚠️ 構造ファイルが見つかりませんでした")
        return
    
    # 各ファイルを分析
    analyses = []
    for i, (structure_id, file_path) in enumerate(structure_files, 1):
        logger.info(f"📋 分析中 ({i}/{len(structure_files)}): {structure_id}")
        analysis = analyze_structure_data(structure_id, file_path)
        analyses.append(analysis)
        
        # 破損ファイルの場合は詳細ログ
        if analysis.get("overall_status") == "corrupted":
            logger.warning(f"⚠️ 破損ファイルを検出: {structure_id}")
            if analysis.get("structure_field_analysis", {}).get("error_details"):
                logger.warning(f"  - structure: {analysis['structure_field_analysis']['error_details']}")
            if analysis.get("gemini_output_analysis", {}).get("error_details"):
                logger.warning(f"  - gemini_output: {analysis['gemini_output_analysis']['error_details']}")
    
    # レポートを生成
    report = generate_report(analyses)
    
    # レポートを保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"corrupted_structures_report_{timestamp}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"📝 レポートを保存: {report_file}")
    
    # 結果を表示
    corrupted_count = sum(1 for a in analyses if a.get("overall_status") == "corrupted")
    logger.info(f"📊 スキャン完了: 破損ファイル {corrupted_count}個 を検出")
    
    if corrupted_count > 0:
        logger.warning("⚠️ 破損ファイルが検出されました。レポートを確認してください。")
        return False
    else:
        logger.info("✅ 破損ファイルは検出されませんでした。")
        return True

if __name__ == "__main__":
    import re
    success = main()
    sys.exit(0 if success else 1) 