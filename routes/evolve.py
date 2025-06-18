from flask import Blueprint, render_template, flash, redirect, url_for
import scripts.evolve_batch as evolve_batch_module

evolve_bp = Blueprint('evolve', __name__, url_prefix='/evolve')

@evolve_bp.route('/')
def index():
    return render_template("evolve/index.html")

@evolve_bp.route('/start')
def start_evolution():
    try:
        evolve_batch_module.run_evolution_loop()
        flash("自動進化ループを実行しました。", "success")
    except Exception as e:
        flash(f"自動進化ループでエラーが発生しました: {e}", "danger")
    return redirect(url_for('index'))  # 適宜トップページなどに変更
