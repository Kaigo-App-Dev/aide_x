# utils/history_utils.py

import json
import os
from datetime import datetime

def extract_score_history(structure_id, history_dir='data/history'):
    """
    指定されたstructure_idに対応する履歴ファイルを走査し、
    スコア推移のリスト（時系列順）を返す。
    """
    score_history = []

    for filename in os.listdir(history_dir):
        if filename.endswith('.json') and structure_id in filename:
            with open(os.path.join(history_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                entry = {
                    'timestamp': data.get('timestamp'),
                    'intent_match': data.get('intent_match'),
                    'quality_score': data.get('quality_score')
                }
                if all(entry.values()):
                    score_history.append(entry)

    # 時系列順にソート
    score_history.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))
    return score_history
