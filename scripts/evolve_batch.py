import sys
import os
import logging

# 親ディレクトリをモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.structure_utils import get_candidates_for_evolution, save_structure
from utils.chatgpt_utils import generate_improvement
from utils.claude_utils import get_claude_intent_reason

# ログ設定
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, 'evolve.log')
logging.basicConfig(
    filename=log_path,
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# 自動採用（上書き）しきい値
ADOPT_THRESHOLD = 0.90

def run_evolution_loop(threshold=0.85):
    print("🔁 自動進化ループ開始")
    logging.info("自動進化ループ開始")

    candidates = get_candidates_for_evolution(threshold=threshold)
    print(f"🧠 対象テンプレート数: {len(candidates)} 件")
    logging.info(f"対象テンプレート数: {len(candidates)} 件")

    for item in candidates:
        id = item["id"]
        print(f"▶ 改善対象: {id}")
        logging.info(f"改善対象: {id}")

        try:
            improved = generate_improvement(item)
            new_id = id + "_evolved"

            improved["source"] = "evolved"
            save_structure(new_id, improved)

            evaluation = get_claude_intent_reason(improved)
            improved.update(evaluation)

            save_structure(new_id, improved)

            print(f"✅ {new_id} 保存・評価完了\n")
            logging.info(f"{new_id} 保存・評価完了")

            # intent_match が一定以上なら元構成に自動採用（上書き）
            intent_match_score = improved.get("intent_match", 0)
            if intent_match_score >= ADOPT_THRESHOLD:
                save_structure(id, improved)
                msg = f"{id} を自動採用（元構成を上書き）しました。"
                print(f"🔄 {msg}")
                logging.info(msg)

        except Exception as e:
            err_msg = f"処理失敗: {id} → {str(e)}"
            print(f"❌ {err_msg}")
            logging.error(err_msg)

    print("🎉 自動進化ループ完了")
    logging.info("自動進化ループ完了")

if __name__ == "__main__":
    run_evolution_loop()
