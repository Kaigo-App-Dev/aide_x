"""
Claude AIプロバイダー

このモジュールは、AnthropicのClaudeモデルを使用するためのプロバイダーを提供します。
"""

import logging
from anthropic import Anthropic
from src.llm.providers.base import BaseLLMProvider, ChatMessage
from src.llm.providers.types import AIProviderResponse
from src.exceptions import ClaudeAPIError, PromptNotFoundError, ResponseFormatError, APIRequestError
from src.utils.logging import save_log
from src.llm.prompts.manager import PromptManager
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from src.exceptions import ProviderInitializationError, APIKeyMissingError

logger = logging.getLogger(__name__)

class ClaudeProvider(BaseLLMProvider):
    """Claude AIプロバイダークラス"""
    
    def __init__(self, prompt_manager: PromptManager, api_key: Optional[str] = None):
        """
        ClaudeProviderの初期化
        
        Args:
            prompt_manager (PromptManager): プロンプト管理インスタンス（必須）
            api_key (Optional[str]): Anthropic APIキー（環境変数ANTHROPIC_API_KEYからも取得可能）
            
        Raises:
            ProviderInitializationError: prompt_managerが指定されていない場合
            APIKeyMissingError: APIキーが見つからない場合
        """
        if prompt_manager is None:
            error_msg = "PromptManager instance is required"
            logger.error(error_msg)
            raise ProviderInitializationError("claude", error_msg)
        self.prompt_manager = prompt_manager
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.error("ANTHROPIC_API_KEY environment variable is not set")
            raise APIKeyMissingError("claude", ["ANTHROPIC_API_KEY"])
        
        self.client = Anthropic(api_key=self.api_key)
        self.model_name = "claude-3-opus-20240229"
        logger.info("ClaudeProvider initialized with PromptManager and API Key")
        super().__init__(model=self.model_name)
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        プロンプトに対する応答を生成
        
        Args:
            prompt (str): 入力プロンプト
            **kwargs: 追加のパラメータ
            
        Returns:
            str: 生成された応答
        """
        try:
            response = self.client.messages.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024)
            )
            return response.content[0].text
        except Exception as e:
            error_msg = f"Claude: API request error: {str(e)}"
            save_log(
                "Claude API error",
                logging.ERROR,
                {
                    "model": self.model_name,
                    "error": error_msg
                }
            )
            raise APIRequestError(error_msg)
    
    def get_template(self, template_name: str) -> Optional[str]:
        """
        指定されたテンプレートを取得
        
        Args:
            template_name (str): テンプレート名
            
        Returns:
            Optional[str]: テンプレート文字列、存在しない場合はNone
        """
        return self.prompt_manager.get_template("claude", template_name)

    def chat(self, prompt: 'Prompt', model_name: str, prompt_manager: 'PromptManager', **kwargs) -> str:
        """
        Claude用の統一chatインターフェース
        Args:
            prompt (Prompt): プロンプトテンプレート
            model_name (str): モデル名
            prompt_manager (PromptManager): プロンプトマネージャ
            **kwargs: 追加パラメータ
        Returns:
            str: 生成された応答
        """
        try:
            prompt_str = prompt.format(**kwargs)
            save_log(
                "Claude API request",
                logging.INFO,
                {
                    "model": model_name,
                    "prompt": prompt_str
                }
            )
            response = self.client.messages.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt_str}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024)
            )
            if not response or not response.content:
                raise ResponseFormatError("Claude: Response format error.")
            save_log(
                "Claude API response",
                logging.INFO,
                {
                    "model": model_name,
                    "result": response.content[0].text
                }
            )
            return response.content[0].text
        except ResponseFormatError as e:
            save_log(
                "Claude API error",
                logging.ERROR,
                {
                    "model": model_name,
                    "error": str(e)
                }
            )
            raise
        except Exception as e:
            error_msg = f"Claude: API request error: {str(e)}"
            save_log(
                "Claude API error",
                logging.ERROR,
                {
                    "model": model_name,
                    "error": error_msg
                }
            )
            raise APIRequestError(error_msg)

def call_claude_api(
    messages: List[Dict[str, str]],
    model: str = "claude-3-opus-20240229",
    temperature: float = 0.5
) -> Dict[str, Any]:
    """
    Claude APIにリクエストを送信し、レスポンスを取得する
    
    Args:
        messages (List[Dict[str, str]]): メッセージのリスト
        model (str, optional): 使用するモデル名. デフォルトは "claude-3-opus-20240229"
        temperature (float, optional): 生成の多様性を制御するパラメータ. デフォルトは 0.5
        
    Returns:
        Dict[str, Any]: APIレスポンスのJSONデータ
        
    Raises:
        requests.exceptions.RequestException: APIリクエストに失敗した場合
        ValueError: APIキーが設定されていない場合
    """
    # APIキーの取得
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    
    # APIエンドポイント
    url = "https://api.anthropic.com/v1/messages"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    # リクエストボディ
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4096
    }
    
    try:
        # APIリクエストの送信
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # エラーステータスの場合は例外を発生
        
        # レスポンスの解析
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Claude API request failed: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude API response: {str(e)}")
        raise ValueError(f"Invalid response from Claude API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Claude API call: {str(e)}")
        raise

def call_claude_evaluation(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Claudeを使用して構成評価を行う
    
    Args:
        messages (List[Dict[str, str]]): 評価用のメッセージリスト
        
    Returns:
        Dict[str, Any]: 評価結果（JSONパース済み）
                      エラー時は空の辞書を返す
    """
    try:
        # Claude APIを呼び出し
        response = call_claude_api(
            messages=messages,
            model="claude-3-opus-20240229",
            temperature=0.2  # 評価では低めのtemperatureを使用
        )
        
        # レスポンスから評価結果を取得
        if "content" in response and len(response["content"]) > 0:
            content = response["content"][0]
            if "text" in content:
                # JSON文字列をパース
                try:
                    return json.loads(content["text"])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse evaluation result as JSON: {str(e)}")
                    return {}
        
        logger.warning("Invalid response format from Claude API")
        return {}
        
    except Exception as e:
        logger.error(f"Error in Claude evaluation: {str(e)}")
        return {}

__all__ = [
    'call_claude_api',
    'call_claude_evaluation'
]
