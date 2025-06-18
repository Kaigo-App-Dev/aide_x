from flask import render_template, request, jsonify
from . import evolve_bp

@evolve_bp.route('/')
def index():
    return render_template('evolve/index.html')

@evolve_bp.route('/generate', methods=['POST'])
def generate_evolution():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'error': 'プロンプトが空です'}), 400
            
        # TODO: 進化生成の実装
        return jsonify({'evolution': '進化の内容'})
        
    except Exception as e:
        return jsonify({'error': '進化の生成中にエラーが発生しました'}), 500 