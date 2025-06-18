"""
Structure Feedback Engine
"""

import logging
from typing import Dict, Any, List, Optional
from src.exceptions import AIProviderError
from src.llm.controller import AIController
from src.logger import save_log
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class StructureFeedbackEngine:
    """構造フィードバックエンジン"""
    
    def __init__(self, controller: AIController):
        """初期化"""
        self.controller = controller
        self.save_log = save_log
    
    def evaluate_structure(self, structure: Dict[str, Any], provider: str = "claude") -> Dict[str, Any]:
        """構造を評価する"""
        try:
            # プロンプトの準備
            prompt = f"""
            以下の構造を評価し、改善点を提案してください。
            構造:
            {json.dumps(structure, ensure_ascii=False, indent=2)}
            
            評価結果は以下のJSON形式で返してください:
            {{
                "score": 0-100の数値,
                "feedback": "改善提案のリスト",
                "suggestions": [
                    {{
                        "component": "改善対象のコンポーネント名",
                        "current": "現在の状態",
                        "suggestion": "改善提案"
                    }}
                ]
            }}
            """
            
            # プロバイダーの呼び出し
            response = self.controller.call(
                provider=provider,
                prompt=prompt,
                expect_json=True
            )
            
            if not response or "error" in response:
                raise AIProviderError(f"Failed to get evaluation from {provider}")
            
            result = response["content"]
            
            # 差分ログの保存
            self._save_diff_log(structure, result, provider)
            
            return result
            
        except Exception as e:
            logger.error(f"Structure evaluation failed: {e}")
            raise
    
    def _save_diff_log(self, original: Dict[str, Any], feedback: Dict[str, Any], provider: str):
        """差分ログを保存する"""
        try:
            # ログディレクトリの作成
            log_dir = f"logs/claude_gemini_diff"
            os.makedirs(log_dir, exist_ok=True)
            
            # ログファイル名の生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"{log_dir}/diff_{provider}_{timestamp}.json"
            
            # 差分ログの作成
            diff_log = {
                "timestamp": datetime.now().isoformat(),
                "provider": provider,
                "original": original,
                "feedback": feedback
            }
            
            # ログの保存
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(diff_log, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save diff log: {e}")
    
    def compare_providers(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """複数のプロバイダーで評価を比較する"""
        results = {}
        for provider in ["claude", "gemini"]:
            try:
                results[provider] = self.evaluate_structure(structure, provider)
            except Exception as e:
                logger.error(f"Evaluation failed for {provider}: {e}")
                results[provider] = {"error": str(e)}
        return results 