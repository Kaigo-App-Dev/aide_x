import os
import json
from glob import glob
from typing import cast, Dict, Any, List
from flask import Blueprint, render_template, request, jsonify
from src.structure.utils import load_structure_by_id, save_structure, StructureDict
from src.structure.history_manager import get_history_diff_data
import logging

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__, url_prefix='/logs')

@logs_bp.route('/structure/<structure_id>')
def view_structure_history(structure_id):
    """
    構成IDごとの評価・補完履歴を表示
    """
    # 構成データ（タイトル表示用）
    structure = load_structure_by_id(structure_id)
    # 履歴ファイルパス
    history_dir = os.path.join('logs', 'structure_history')
    pattern = os.path.join(history_dir, f'{structure_id}_*.json')
    files = sorted(glob(pattern), reverse=True)
    history = []
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                history.append(data)
        except Exception:
            continue
    return render_template(
        'logs/structure_history.html',
        structure_id=structure_id,
        structure=structure,
        history=history
    )

@logs_bp.route('/apply/<structure_id>', methods=['POST'])
def apply_history(structure_id):
    """
    指定されたタイムスタンプの履歴を再適用
    """
    try:
        data = request.get_json()
        timestamp = data.get('timestamp')
        
        if not timestamp:
            return jsonify({'success': False, 'error': 'タイムスタンプが指定されていません'})
        
        # 履歴ファイルを検索
        history_dir = os.path.join('logs', 'structure_history')
        pattern = os.path.join(history_dir, f'{structure_id}_{timestamp[:8]}_*.json')
        files = glob(pattern)
        
        if not files:
            return jsonify({'success': False, 'error': '指定された履歴が見つかりません'})
        
        # タイムスタンプに最も近いファイルを選択
        target_file = None
        for f in files:
            try:
                with open(f, encoding='utf-8') as fp:
                    data = json.load(fp)
                    if data.get('timestamp') == timestamp:
                        target_file = f
                        break
            except Exception:
                continue
        
        if not target_file:
            return jsonify({'success': False, 'error': '指定されたタイムスタンプの履歴が見つかりません'})
        
        # 履歴ファイルから構成データを読み込み
        with open(target_file, encoding='utf-8') as fp:
            history_data = json.load(fp)
        
        # 現在の構成を読み込み
        current_structure = load_structure_by_id(structure_id)
        if not current_structure:
            return jsonify({'success': False, 'error': '現在の構成が見つかりません'})
        
        # 履歴から評価・補完データを復元
        if 'evaluations' in history_data:
            current_structure['evaluations'] = history_data['evaluations']
        if 'completions' in history_data:
            current_structure['completions'] = history_data['completions']
        
        # 構成を保存
        save_structure(structure_id, cast(StructureDict, current_structure))
        
        return jsonify({'success': True, 'message': '履歴を再適用しました'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'再適用中にエラーが発生しました: {str(e)}'})

@logs_bp.route('/diff/<structure_id>')
def view_structure_diff(structure_id):
    """
    2つの履歴バージョンの差分を表示
    """
    v1_timestamp = request.args.get('v1')
    v2_timestamp = request.args.get('v2')
    
    if not v1_timestamp or not v2_timestamp:
        return render_template(
            'logs/structure_diff.html',
            structure_id=structure_id,
            structure=load_structure_by_id(structure_id),
            diff_data=None,
            v1_timestamp=None,
            v2_timestamp=None
        )
    
    # 履歴ファイルを読み込み
    history_dir = os.path.join('logs', 'structure_history')
    
    def load_history_data(timestamp):
        pattern = os.path.join(history_dir, f'{structure_id}_{timestamp[:8]}_*.json')
        files = glob(pattern)
        for f in files:
            try:
                with open(f, encoding='utf-8') as fp:
                    data = json.load(fp)
                    if data.get('timestamp') == timestamp:
                        return data
            except Exception:
                continue
        return None
    
    v1_data = load_history_data(v1_timestamp)
    v2_data = load_history_data(v2_timestamp)
    
    if not v1_data or not v2_data:
        return render_template(
            'logs/structure_diff.html',
            structure_id=structure_id,
            structure=load_structure_by_id(structure_id),
            diff_data=None,
            v1_timestamp=v1_timestamp,
            v2_timestamp=v2_timestamp
        )
    
    # 差分データを生成
    diff_data = generate_diff_data(v1_data, v2_data)
    
    return render_template(
        'logs/structure_diff.html',
        structure_id=structure_id,
        structure=load_structure_by_id(structure_id),
        diff_data=diff_data,
        v1_timestamp=v1_timestamp,
        v2_timestamp=v2_timestamp
    )

def generate_diff_data(v1_data: Dict[str, Any], v2_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    2つの履歴データの差分を生成
    """
    def json_to_lines(data: Dict[str, Any]) -> List[str]:
        """JSONデータを行のリストに変換"""
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return json_str.split('\n')
    
    v1_lines = json_to_lines(v1_data)
    v2_lines = json_to_lines(v2_data)
    
    # 簡単な差分アルゴリズム（行単位での比較）
    diff_lines = []
    v1_diff_lines = []
    v2_diff_lines = []
    
    # 最大行数
    max_lines = max(len(v1_lines), len(v2_lines))
    
    for i in range(max_lines):
        v1_line = v1_lines[i] if i < len(v1_lines) else ""
        v2_line = v2_lines[i] if i < len(v2_lines) else ""
        
        if v1_line == v2_line:
            # 変更なし
            v1_diff_lines.append({'type': 'unchanged', 'content': v1_line})
            v2_diff_lines.append({'type': 'unchanged', 'content': v2_line})
        else:
            # 変更あり
            if v1_line:
                v1_diff_lines.append({'type': 'removed', 'content': v1_line})
            if v2_line:
                v2_diff_lines.append({'type': 'added', 'content': v2_line})
    
    # 統計を計算
    added_count = sum(1 for line in v2_diff_lines if line['type'] == 'added')
    removed_count = sum(1 for line in v1_diff_lines if line['type'] == 'removed')
    unchanged_count = sum(1 for line in v1_diff_lines if line['type'] == 'unchanged')
    
    return {
        'v1_lines': v1_diff_lines,
        'v2_lines': v2_diff_lines,
        'added_count': added_count,
        'removed_count': removed_count,
        'unchanged_count': unchanged_count
    }

@logs_bp.route('/structure/<structure_id>/evaluations')
def view_evaluation_history(structure_id):
    """
    構成IDごとの評価履歴一覧を表示
    """
    # 構成データ（タイトル表示用）
    structure = load_structure_by_id(structure_id)
    # 履歴ファイルパス
    history_dir = os.path.join('logs', 'structure_history')
    pattern = os.path.join(history_dir, f'{structure_id}_*.json')
    files = sorted(glob(pattern), reverse=True)
    
    evaluations = []
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                if 'evaluations' in data and data['evaluations']:
                    for eval_item in data['evaluations']:
                        eval_item['history_timestamp'] = data.get('timestamp', '')
                        eval_item['history_file'] = os.path.basename(f)
                        evaluations.append(eval_item)
        except Exception:
            continue
    
    return render_template(
        'logs/evaluation_history.html',
        structure_id=structure_id,
        structure=structure,
        evaluations=evaluations
    )

@logs_bp.route('/structure/<structure_id>/completions')
def view_completion_history(structure_id):
    """
    構成IDごとの補完履歴一覧を表示
    """
    # 構成データ（タイトル表示用）
    structure = load_structure_by_id(structure_id)
    # 履歴ファイルパス
    history_dir = os.path.join('logs', 'structure_history')
    pattern = os.path.join(history_dir, f'{structure_id}_*.json')
    files = sorted(glob(pattern), reverse=True)
    
    completions = []
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                if 'completions' in data and data['completions']:
                    for comp_item in data['completions']:
                        comp_item['history_timestamp'] = data.get('timestamp', '')
                        comp_item['history_file'] = os.path.basename(f)
                        completions.append(comp_item)
        except Exception:
            continue
    
    return render_template(
        'logs/completion_history.html',
        structure_id=structure_id,
        structure=structure,
        completions=completions
    )

@logs_bp.route('/evaluations')
def all_evaluations():
    """
    すべての構成の評価履歴一覧
    """
    history_dir = os.path.join('logs', 'structure_history')
    pattern = os.path.join(history_dir, f'*_*.json')
    files = sorted(glob(pattern), reverse=True)
    evaluations = []
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                structure_id = data.get('id') or os.path.basename(f).split('_')[0]
                title = data.get('title', '')
                if 'evaluations' in data and data['evaluations']:
                    for eval_item in data['evaluations']:
                        evaluations.append({
                            'structure_id': structure_id,
                            'title': title,
                            'timestamp': eval_item.get('timestamp', data.get('timestamp', '')),
                            'score': eval_item.get('score'),
                            'feedback': eval_item.get('feedback'),
                        })
        except Exception:
            continue
    # 日時降順
    evaluations.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('logs/all_evaluations.html', evaluations=evaluations)

@logs_bp.route('/completions')
def all_completions():
    """
    すべての構成の補完履歴一覧
    """
    history_dir = os.path.join('logs', 'structure_history')
    pattern = os.path.join(history_dir, f'*_*.json')
    files = sorted(glob(pattern), reverse=True)
    completions = []
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                structure_id = data.get('id') or os.path.basename(f).split('_')[0]
                title = data.get('title', '')
                if 'completions' in data and data['completions']:
                    for comp_item in data['completions']:
                        completions.append({
                            'structure_id': structure_id,
                            'title': title,
                            'timestamp': comp_item.get('timestamp', data.get('timestamp', '')),
                            'content': comp_item.get('content'),
                        })
        except Exception:
            continue
    # 日時降順
    completions.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('logs/all_completions.html', completions=completions)

@logs_bp.route('/compare/<structure_id>/<timestamp>')
def compare_evaluation(structure_id, timestamp):
    """
    評価・補完の比較ページ（正式実装）
    指定structure_idの履歴から、指定timestampとその直前構成を比較
    """
    # 履歴ファイルを検索
    history_dir = os.path.join('logs', 'structure_history')
    pattern = os.path.join(history_dir, f'{structure_id}_*.json')
    files = sorted(glob(pattern), reverse=True)
    
    current_data = None
    previous_data = None
    
    # 指定timestampの履歴を検索
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                if data.get('timestamp') == timestamp:
                    current_data = data
                    break
        except Exception:
            continue
    
    # 直前の履歴を検索
    if current_data:
        current_file = None
        for f in files:
            try:
                with open(f, encoding='utf-8') as fp:
                    data = json.load(fp)
                    if data.get('timestamp') == timestamp:
                        current_file = f
                        break
            except Exception:
                continue
        
        if current_file:
            # 現在のファイルの次のファイル（より古い）を取得
            current_index = files.index(current_file)
            if current_index + 1 < len(files):
                try:
                    with open(files[current_index + 1], encoding='utf-8') as fp:
                        previous_data = json.load(fp)
                except Exception:
                    pass
    
    return render_template(
        'logs/compare.html',
        structure_id=structure_id,
        timestamp=timestamp,
        current_data=current_data,
        previous_data=previous_data
    )

@logs_bp.route('/api/structure/<structure_id>')
def get_structure_diff_api(structure_id: str):
    """履歴差分データを取得するAPIエンドポイント"""
    try:
        # クエリパラメータからインデックスを取得
        index = request.args.get('index', 0, type=int)
        
        # 履歴差分データを取得
        diff_data = get_history_diff_data(structure_id, index)
        
        if diff_data is None:
            return jsonify({
                "success": False,
                "error": "履歴データが見つかりません"
            }), 404
            
        return jsonify({
            "success": True,
            "data": diff_data
        })
        
    except Exception as e:
        logger.error(f"履歴差分APIでエラーが発生: {str(e)}")
        return jsonify({
            "success": False,
            "error": "サーバーエラーが発生しました"
        }), 500 