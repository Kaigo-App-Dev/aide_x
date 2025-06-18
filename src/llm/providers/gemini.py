"""
Gemini AIプロバイダー

このモジュールは、GoogleのGeminiモデルを使用するためのプロバイダーを提供します。
"""

import logging
import google.generativeai as genai
from google.generativeai.types import (
    GenerateContentResponse,
    GenerationConfig
)
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from src.llm.providers.base import BaseLLMProvider, ChatMessage
from src.llm.providers.types import AIProviderResponse
from src.common.exceptions import GeminiAPIError, PromptNotFoundError, ResponseFormatError
from src.common.logging_utils import save_log
from src.llm.prompts.manager import PromptManager
import os
import json
import requests
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import yaml
from src.exceptions import ProviderInitializationError, APIKeyMissingError

logger = logging.getLogger(__name__)

def safe_yaml_to_json(yaml_str: str) -> Dict[str, Any]:
    """YAML文字列を安全にJSONに変換する"""
    try:
        # YAMLをパース
        data = yaml.safe_load(yaml_str)
        # JSONに変換して検証
        json_str = json.dumps(data)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"YAML to JSON conversion failed: {e}")
        return {}

def fix_unquoted_keys(json_str: str) -> str:
    """未クオートのJSONキーを修正する"""
    # 未クオートのキーを検出して修正
    pattern = r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:'
    fixed = re.sub(pattern, r'\1"\2":', json_str)
    return fixed

def extract_json_part(text: str) -> Dict[str, Any]:
    """テキストからJSON部分を抽出して解析する"""
    try:
        # JSONブロックを検出
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # JSONブロックが見つからない場合は、テキスト全体を試行
            json_str = text.strip()
        
        # 未クオートキーの修正を試行
        fixed_json = fix_unquoted_keys(json_str)
        
        try:
            # 修正したJSONをパース
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            # YAMLとしてパースを試行
            return safe_yaml_to_json(json_str)
            
    except Exception as e:
        # エラー情報をログに保存
        error_dump = {
            "original_text": text,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        dump_path = f"logs/gemini_error_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(error_dump, f, ensure_ascii=False, indent=2)
        logger.error(f"JSON extraction failed: {e}")
        return {}

class GeminiProvider(BaseLLMProvider):
    """Gemini AIプロバイダークラス"""
    
    def __init__(self, prompt_manager: PromptManager, api_key: Optional[str] = None):
        """
        GeminiProviderの初期化
        
        Args:
            prompt_manager (PromptManager): プロンプト管理インスタンス（必須）
            api_key (Optional[str]): Gemini APIキー（環境変数GEMINI_API_KEYまたはGCP_GEMINI_API_KEYからも取得可能）
            
        Raises:
            ProviderInitializationError: prompt_managerが指定されていない場合
            APIKeyMissingError: APIキーが見つからない場合
        """
        if prompt_manager is None:
            error_msg = "PromptManager instance is required"
            logger.error(error_msg)
            raise ProviderInitializationError("gemini", error_msg)
        self.prompt_manager = prompt_manager
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GCP_GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY or GCP_GEMINI_API_KEY environment variable is not set")
            raise APIKeyMissingError("gemini", ["GEMINI_API_KEY", "GCP_GEMINI_API_KEY"])
        
        logger.info("GeminiProvider initialized with PromptManager and API Key")
        super().__init__(model="gemini-pro")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model)
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        プロンプトに対する応答を生成
        
        Args:
            prompt (str): 入力プロンプト
            **kwargs: 追加のパラメータ
            
        Returns:
            str: 生成された応答
        """
        # TODO: Gemini APIの実装
        return "Gemini response placeholder"
    
    def get_template(self, template_name: str) -> Optional[str]:
        """
        指定されたテンプレートを取得
        
        Args:
            template_name (str): テンプレート名
            
        Returns:
            Optional[str]: テンプレート文字列、存在しない場合はNone
        """
        return self.prompt_manager.get_template("gemini", template_name)

    def call(self, prompt: str, **kwargs) -> AIProviderResponse:
        """Gemini APIを呼び出して応答を返す"""
        try:
            # リクエストログの保存
            save_log(
                "Gemini API request",
                logging.INFO,
                {
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 1024)
                }
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", 0.7),
                    max_output_tokens=kwargs.get("max_tokens", 1024)
                )
            )
            
            if not response or not response.text:
                raise ResponseFormatError("Gemini: Response format error.")
            
            content = response.text
            
            # JSONレスポンスの処理
            if kwargs.get("expect_json", False):
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    raise ResponseFormatError("Gemini: Failed to parse JSON response.")
                
                # レスポンスログの保存
                save_log(
                    "Gemini API response",
                    logging.INFO,
                    {
                        "model": self.model,
                        "result": result,
                        "raw": str(response)
                    }
                )
                
                return AIProviderResponse(
                    content=json.dumps(result),
                    raw=response,
                    provider="gemini",
                    error=None
                )
            
            # 通常レスポンスのログ保存
            save_log(
                "Gemini API response",
                logging.INFO,
                {
                    "model": self.model,
                    "result": content,
                    "raw": str(response)
                }
            )
            
            return AIProviderResponse(
                content=content,
                raw=response,
                provider="gemini",
                error=None
            )
        except ResponseFormatError as e:
            error_msg = f"Gemini: Response format error: {str(e)}"
            save_log(
                "Gemini API error",
                logging.ERROR,
                {
                    "model": self.model,
                    "error": error_msg,
                    "prompt": prompt
                }
            )
            return AIProviderResponse(
                content="",
                raw=None,
                provider="gemini",
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Gemini: API request error: {str(e)}"
            save_log(
                "Gemini API error",
                logging.ERROR,
                {
                    "model": self.model,
                    "error": error_msg,
                    "prompt": prompt
                }
            )
            return AIProviderResponse(
                content="",
                raw=None,
                provider="gemini",
                error=error_msg
            )

    def chat(self, messages: list[ChatMessage]) -> str:
        """チャットメッセージを処理して応答を返す"""
        try:
            # プロンプトの取得とレンダリング
            prompt = self.prompt_manager.get_prompt("gemini", "chat")
            if not prompt:
                raise PromptNotFoundError("Gemini: Prompt not found")
            
            # メッセージを整形
            content = "\n".join([f"{m.role}: {m.content}" for m in messages])
            
            # プロンプトの置換
            try:
                system_prompt = prompt.template.format(user_input=content)
            except KeyError as e:
                logger.error(f"Template format error: {str(e)}")
                raise GeminiAPIError(f"プロンプトのフォーマットエラー: {str(e)}")
            
            # リクエストログの保存
            save_log(
                "Gemini chat request",
                logging.INFO,
                {
                    "model": self.model,
                    "prompt": system_prompt,
                    "messages": [{"role": m.role, "content": m.content} for m in messages]
                }
            )
            
            # APIリクエストの実行
            response = self.model.generate_content(
                system_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024
                )
            )
            
            # レスポンスの検証
            if not response or not response.text:
                raise ResponseFormatError("Gemini: Empty response from API")
            
            content = response.text
            
            # レスポンスログの保存
            save_log(
                "Gemini chat response",
                logging.INFO,
                {
                    "model": self.model,
                    "result": content,
                    "raw": str(response)
                }
            )
            
            return content
        except Exception as e:
            error_msg = f"Gemini: Chat error: {str(e)}"
            save_log(
                "Gemini chat error",
                logging.ERROR,
                {
                    "model": self.model,
                    "error": error_msg,
                    "messages": [{"role": m.role, "content": m.content} for m in messages]
                }
            )
            raise GeminiAPIError(error_msg)

def call_gemini_api(
    messages: List[Dict[str, str]],
    model: str = "gemini-1.5-pro",
    temperature: float = 0.8
) -> str:
    """
    Gemini APIにリクエストを送信し、レスポンスを取得する
    
    Args:
        messages (List[Dict[str, str]]): メッセージのリスト
        model (str, optional): 使用するモデル名. デフォルトは "gemini-1.5-pro"
        temperature (float, optional): 生成の多様性を制御するパラメータ. デフォルトは 0.8
        
    Returns:
        str: APIレスポンスのテキスト
             エラー時は空文字列を返す
        
    Raises:
        ValueError: APIキーが設定されていない場合
    """
    # APIキーの取得
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable is not set")
        return ""
    
    # APIエンドポイント
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # メッセージをGemini形式に変換
    contents = []
    for msg in messages:
        if "role" in msg and "content" in msg:
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["content"]}]
            })
    
    # リクエストボディ
    data = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature
        }
    }
    
    try:
        # APIリクエストの送信
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # エラーステータスの場合は例外を発生
        
        # レスポンスの解析
        result = response.json()
        
        # レスポンスからテキストを抽出
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                if len(parts) > 0 and "text" in parts[0]:
                    return parts[0]["text"]
        
        logger.warning("Invalid response format from Gemini API")
        return ""
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API request failed: {str(e)}")
        return ""
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini API response: {str(e)}")
        return ""
    except KeyError as e:
        logger.error(f"Missing key in Gemini API response: {str(e)}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error in Gemini API call: {str(e)}")
        return ""

__all__ = [
    'call_gemini_api'
] 