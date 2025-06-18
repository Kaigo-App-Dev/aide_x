"""
AIモデル呼び出しハブ

このモジュールは、AIモデルの呼び出しを一元管理するハブを提供します。
"""

from typing import Dict, Any, Optional, List, Sequence, cast
from dataclasses import dataclass
import logging
import json
from .controller import AIController
from .providers.base import ChatMessage
from .prompts import prompt_manager, PromptManager
from src.exceptions import AIProviderError, APIRequestError, ResponseFormatError, PromptNotFoundError
from src.types import AIProviderResponse
from datetime import datetime
from src.llm.providers.base import BaseLLMProvider
from src.llm.providers.claude import ClaudeProvider
from src.llm.providers.gemini import GeminiProvider
from src.utils.logging import save_log

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """LLMの応答の定義"""
    content: str
    error: Optional[str] = None

class LLMHub:
    """LLM Hub - AIプロバイダの一元管理クラス"""
    
    @staticmethod
    def call_model(
        model_name: str,
        prompt_name: str,
        prompt_manager: 'PromptManager',
        **kwargs
    ) -> AIProviderResponse:
        """
        指定されたモデルでプロンプトを実行
        
        Args:
            model_name: モデル名
            prompt_name: プロンプト名
            prompt_manager: プロンプトマネージャ
            **kwargs: テンプレートに渡すパラメータ
            
        Returns:
            AIProviderResponse: モデルの応答
        """
        provider = get_provider(model_name)
        if not provider:
            raise AIProviderError(f"Provider not found: {model_name}")
        prompt = prompt_manager.get(model_name, prompt_name)
        if prompt is None:
            raise PromptNotFoundError(f"Prompt not found: {model_name}.{prompt_name}")
        return provider.chat(prompt, model_name, prompt_manager, **kwargs)
    
    @staticmethod
    def chat(
        provider_name: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        指定されたプロバイダーでチャットを実行
        
        Args:
            provider_name: プロバイダー名
            messages: チャットメッセージのリスト
            temperature: 生成の多様性を制御するパラメータ（0.0-1.0）
            max_tokens: 生成する最大トークン数
            
        Returns:
            LLMResponse: 生成された応答
        """
        return chat(provider_name, messages, temperature, max_tokens)
    
    @staticmethod
    def evaluate_structure(
        provider_name: str,
        structure: Dict[str, Any]
    ) -> LLMResponse:
        """
        指定されたプロバイダーで構成を評価
        
        Args:
            provider_name: プロバイダー名
            structure: 評価する構成
            
        Returns:
            LLMResponse: 評価結果
        """
        return evaluate_structure(provider_name, structure)
    
    @staticmethod
    def generate_structure(
        provider_name: str,
        requirements: str
    ) -> LLMResponse:
        """
        指定されたプロバイダーで構成を生成
        
        Args:
            provider_name: プロバイダー名
            requirements: 生成要件
            
        Returns:
            LLMResponse: 生成された構成
        """
        return generate_structure(provider_name, requirements)

def get_provider(provider_name: str) -> Optional[BaseLLMProvider]:
    """
    プロバイダ名からプロバイダインスタンスを取得する
    
    Args:
        provider_name (str): プロバイダ名（"claude" または "gemini"）
        
    Returns:
        Optional[BaseLLMProvider]: プロバイダインスタンス、存在しない場合はNone
    """
    if provider_name == "claude":
        return ClaudeProvider(prompt_manager)
    elif provider_name == "gemini":
        return GeminiProvider(prompt_manager)
    return None

def call_model(provider_name: str, model_name: str, prompt_name: str, prompt_manager: 'PromptManager', **kwargs) -> str:
    """
    AIモデルを呼び出して応答を取得する
    Args:
        provider_name (str): プロバイダ名
        model_name (str): モデル名
        prompt_name (str): プロンプト名
        prompt_manager (PromptManager): プロンプトマネージャ
        **kwargs: テンプレートに渡すパラメータ
    Returns:
        str: 生成された応答
    """
    provider = get_provider(provider_name)
    if not provider:
        raise AIProviderError(f"Provider not found: {provider_name}")
    prompt = prompt_manager.get(provider_name, prompt_name)
    if prompt is None:
        raise PromptNotFoundError(f"Prompt not found: {provider_name}.{prompt_name}")
    return provider.chat(prompt, model_name, prompt_manager, **kwargs)

def chat(
    provider_name: str,
    messages: List[ChatMessage],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> LLMResponse:
    """
    指定されたプロバイダーでチャットを実行
    
    Args:
        provider_name: プロバイダー名
        messages: チャットメッセージのリスト
        temperature: 生成の多様性を制御するパラメータ（0.0-1.0）
        max_tokens: 生成する最大トークン数
        
    Returns:
        LLMResponse: 生成された応答
    """
    try:
        response = AIController.call(
            provider=provider_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return LLMResponse(content=response.get("content", ""))
        
    except (APIRequestError, ResponseFormatError) as e:
        logger.error(f"Error in chat with {provider_name}: {str(e)}")
        return LLMResponse(content="", error=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat with {provider_name}: {str(e)}")
        return LLMResponse(content="", error=str(e))

def evaluate_structure(
    provider_name: str,
    structure: Dict[str, Any]
) -> LLMResponse:
    """
    指定されたプロバイダーで構成を評価
    
    Args:
        provider_name: プロバイダー名
        structure: 評価する構成
        
    Returns:
        LLMResponse: 評価結果
    """
    try:
        prompt_manager.register_builtin_templates()
        evaluation_template = prompt_manager.get_prompt(provider_name, "evaluation_template")
        if not evaluation_template:
            raise ValueError(f"Evaluation template not found for {provider_name}")
        
        # プロンプトをレンダリング
        prompt = evaluation_template.render(
            title=structure.get("title", ""),
            description=structure.get("description", ""),
            content=structure.get("content", {})
        )
        
        messages = [
            ChatMessage(role="user", content=prompt)
        ]
        
        response = AIController.call(
            provider=provider_name,
            messages=messages
        )
        
        return LLMResponse(content=response.get("content", ""))
        
    except (APIRequestError, ResponseFormatError) as e:
        logger.error(f"Error in structure evaluation with {provider_name}: {str(e)}")
        return LLMResponse(content="", error=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in structure evaluation with {provider_name}: {str(e)}")
        return LLMResponse(content="", error=str(e))

def generate_structure(
    provider_name: str,
    requirements: str
) -> LLMResponse:
    """
    指定されたプロバイダーで構成を生成
    
    Args:
        provider_name: プロバイダー名
        requirements: 生成要件
        
    Returns:
        LLMResponse: 生成された構成
    """
    try:
        prompt_manager.register_builtin_templates()
        generation_template = prompt_manager.get_prompt(provider_name, "generation_template")
        if not generation_template:
            raise ValueError(f"Generation template not found for {provider_name}")
        
        # プロンプトをレンダリング
        prompt = generation_template.render(requirements=requirements)
        
        messages = [
            ChatMessage(role="user", content=prompt)
        ]
        
        response = AIController.call(
            provider=provider_name,
            messages=messages
        )
        
        return LLMResponse(content=response.get("content", ""))
        
    except (APIRequestError, ResponseFormatError) as e:
        logger.error(f"Error in structure generation with {provider_name}: {str(e)}")
        return LLMResponse(content="", error=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in structure generation with {provider_name}: {str(e)}")
        return LLMResponse(content="", error=str(e))

def safe_generate_and_evaluate(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    安全に構成を生成して評価する
    
    Args:
        chat_history: チャット履歴
        
    Returns:
        Dict[str, Any]: 生成された構成と評価結果
    """
    try:
        # チャット履歴から要件を抽出
        requirements = "\n".join([
            msg["content"] for msg in chat_history
            if msg["role"] == "user"
        ])
        
        # 構成を生成
        response = generate_structure("claude", requirements)
        if response.error:
            raise ValueError(f"Generation failed: {response.error}")
        
        # 生成された構成をパース
        try:
            structure = json.loads(response.content)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse generated structure")
        
        # 構成を評価
        eval_response = evaluate_structure("claude", structure)
        if eval_response.error:
            raise ValueError(f"Evaluation failed: {eval_response.error}")
        
        # 評価結果をパース
        try:
            evaluation = json.loads(eval_response.content)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse evaluation result")
        
        return {
            "structure": structure,
            "evaluation": evaluation
        }
        
    except Exception as e:
        logger.error(f"Error in safe_generate_and_evaluate: {str(e)}")
        return {
            "structure": None,
            "evaluation": None,
            "error": str(e)
        }

def normalize_structure_format(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生のデータを正規化された構造形式に変換
    
    Args:
        raw_data: 生のデータ
        
    Returns:
        Dict[str, Any]: 正規化された構造
    """
    try:
        # 基本的な構造を確保
        structure = {
            "title": raw_data.get("title", "Untitled"),
            "description": raw_data.get("description", ""),
            "content": raw_data.get("content", {}),
            "metadata": raw_data.get("metadata", {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # contentが文字列の場合はJSONとしてパース
        if isinstance(structure["content"], str):
            try:
                structure["content"] = json.loads(structure["content"])
            except json.JSONDecodeError:
                structure["content"] = {"raw": structure["content"]}
        
        return structure
        
    except Exception as e:
        logger.error(f"Error in normalize_structure_format: {str(e)}")
        return {
            "title": "Error",
            "description": f"Failed to normalize structure: {str(e)}",
            "content": {"error": str(e)},
            "metadata": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        } 