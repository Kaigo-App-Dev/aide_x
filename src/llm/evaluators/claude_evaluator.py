"""
Claude用の構造評価モジュール
"""

import logging
from typing import Dict, Any
from src.llm.controller import AIController
from src.llm.evaluator import EvaluationResult
from src.exceptions import ProviderError, PromptError

logger = logging.getLogger(__name__)

class ClaudeEvaluator:
    """Claudeを使用した構造評価クラス"""
    
    def __init__(self):
        """ClaudeEvaluatorの初期化"""
        self.controller = AIController()
    
    def evaluate(self, structure: Dict[str, Any]) -> EvaluationResult:
        """
        構造を評価
        
        Args:
            structure (Dict[str, Any]): 評価対象の構造
            
        Returns:
            EvaluationResult: 評価結果
            
        Raises:
            ProviderError: プロバイダーの初期化や実行に失敗した場合
            PromptError: プロンプトの取得やフォーマットに失敗した場合
        """
        try:
            # プロンプトの取得とフォーマット
            prompt = self.controller.get_provider("claude").get_template("structure_evaluation")
            if not prompt:
                raise PromptError("claude", "structure_evaluation", "Template not found")
            
            formatted_prompt = prompt.format(structure=structure)
            
            # 評価の実行
            response = self.controller.generate_response("claude", formatted_prompt)
            if not response:
                return EvaluationResult(
                    is_valid=False,
                    error="Empty response from Claude",
                    details={"prompt": formatted_prompt}
                )
            
            # レスポンスの解析
            try:
                score = float(response.get("score", 0.0))
                is_valid = bool(response.get("is_valid", False))
                return EvaluationResult(
                    is_valid=is_valid,
                    score=score,
                    details={
                        "prompt": formatted_prompt,
                        "response": response
                    }
                )
            except (ValueError, TypeError) as e:
                return EvaluationResult(
                    is_valid=False,
                    error=f"Invalid response format: {str(e)}",
                    details={
                        "prompt": formatted_prompt,
                        "response": response
                    }
                )
                
        except ProviderError as e:
            logger.error(f"Provider error in Claude evaluation: {str(e)}")
            return EvaluationResult(
                is_valid=False,
                error=f"Provider error: {str(e)}"
            )
        except PromptError as e:
            logger.error(f"Prompt error in Claude evaluation: {str(e)}")
            return EvaluationResult(
                is_valid=False,
                error=f"Prompt error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Claude evaluation: {str(e)}")
            return EvaluationResult(
                is_valid=False,
                error=f"Unexpected error: {str(e)}"
            ) 