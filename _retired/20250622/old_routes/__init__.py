from .chat.chat import chat_bp
from .structure.base_routes import structure_bp
from .evolve import evolve_bp
from .preview.routes import preview_bp

all_blueprints = [
    chat_bp,
    structure_bp,
    evolve_bp,
    preview_bp,
    # 必要に応じて他のbpも追加
]
