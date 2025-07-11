"""
ChatGPT AIプロバイダー

このモジュールは、OpenAIのChatGPTモデルを使用するためのプロバイダーを提供します。
"""

import logging
import openai
from openai.types.chat import ChatCompletion
from src.llm.providers.base import BaseLLMProvider, ChatMessage
from src.types import AIProviderResponse, MessageParamList
from src.exceptions import ChatGPTAPIError, PromptNotFoundError, ResponseFormatError, APIRequestError
from src.utils.logging import save_log
from src.llm.prompts.manager import PromptManager
import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import re
import yaml
import requests
from src.exceptions import ProviderInitializationError, APIKeyMissingError
import time

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
        dump_path = f"logs/chatgpt_error_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(error_dump, f, ensure_ascii=False, indent=2)
        logger.error(f"JSON extraction failed: {e}")
        return {}

class ChatGPTProvider(BaseLLMProvider):
    """ChatGPT AIプロバイダークラス"""
    
    def __init__(self, prompt_manager: PromptManager, api_key: Optional[str] = None):
        """
        ChatGPTProviderの初期化
        
        Args:
            prompt_manager (PromptManager): プロンプト管理インスタンス（必須）
            api_key (Optional[str]): OpenAI APIキー（環境変数OPENAI_API_KEYからも取得可能）
            
        Raises:
            ProviderInitializationError: prompt_managerが指定されていない場合
            APIKeyMissingError: APIキーが見つからない場合
        """
        super().__init__(model="gpt-4")
        if prompt_manager is None:
            error_msg = "PromptManager instance is required"
            logger.error(error_msg)
            raise ProviderInitializationError("chatgpt", error_msg)
        self.prompt_manager = prompt_manager
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            raise APIKeyMissingError("chatgpt", ["OPENAI_API_KEY"])
        
        logger.info("ChatGPTProvider initialized with PromptManager and API Key")
    
    def call(self, messages: List[Dict[str, str]], **kwargs) -> AIProviderResponse:
        """
        ChatGPT APIを呼び出して応答を取得
        
        Args:
            messages (List[Dict[str, str]]): メッセージのリスト
            **kwargs: 追加のパラメータ
            
        Returns:
            AIProviderResponse: 生成された応答
            
        Raises:
            APIRequestError: APIリクエストが失敗した場合
            ResponseFormatError: レスポンスの形式が不正な場合
        """
        logger.info("ChatGPT API call started")
        logger.debug(f"ChatGPT messages: {messages}")
        
        try:
            # OpenAIクライアントの初期化
            client = openai.OpenAI(api_key=self.api_key)
            
            # メッセージ形式の変換
            openai_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    openai_messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
                else:
                    logger.warning(f"Invalid message format: {msg}")
                    continue
            
            logger.debug(f"OpenAI messages: {openai_messages}")
            
            # ChatGPT API呼び出し
            start_time = time.monotonic()
            response = client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            
            end_time = time.monotonic()
            duration = end_time - start_time
            logger.info(f"✅ ChatGPT API call finished in {duration:.2f} seconds.")
            
            # レスポンスの処理
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content or ""
                logger.info(f"ChatGPT API call successful: {content[:100]}...")
                logger.debug(f"ChatGPT full response: {content}")
                
                # 応答の妥当性確認
                if not content or not content.strip():
                    error_msg = "ChatGPT returned empty or whitespace-only response"
                    logger.error(error_msg)
                    raise ResponseFormatError("chatgpt", error_msg)
                
                # JSON形式の応答かどうかを簡易チェック
                if "structure_generation" in str(messages) and not any(marker in content for marker in ["{", "```json", "title", "content"]):
                    logger.warning("ChatGPT response may not contain valid JSON structure")
                    logger.debug(f"Response content: {content}")
                
                return {
                    "content": content,
                    "model": self.model,
                    "provider": "chatgpt",
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
                    }
                }
            else:
                error_msg = "ChatGPT API returned empty response"
                logger.error(error_msg)
                raise ResponseFormatError("chatgpt", error_msg)
                
        except openai.AuthenticationError as e:
            error_msg = f"ChatGPT API authentication failed: {str(e)}"
            logger.error(error_msg)
            raise APIRequestError("chatgpt", error_msg)
        except openai.RateLimitError as e:
            error_msg = f"ChatGPT API rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise APIRequestError("chatgpt", error_msg)
        except openai.APIError as e:
            error_msg = f"ChatGPT API error: {str(e)}"
            logger.error(error_msg)
            raise APIRequestError("chatgpt", error_msg)
        except Exception as e:
            error_msg = f"ChatGPT API call failed: {str(e)}"
            logger.error(error_msg)
            raise APIRequestError("chatgpt", error_msg)
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        プロンプトに対する応答を生成
        
        Args:
            prompt (str): 入力プロンプト
            **kwargs: 追加のパラメータ
            
        Returns:
            str: 生成された応答
        """
        # TODO: ChatGPT APIの実装
        return "ChatGPT response placeholder"
    
    def get_template(self, template_name: str) -> Optional[str]:
        """
        指定されたテンプレートを取得
        
        Args:
            template_name (str): テンプレート名
            
        Returns:
            Optional[str]: テンプレート文字列、存在しない場合はNone
        """
        return self.prompt_manager.get_template("chatgpt", template_name)

    def chat(
        self,
        messages: List[ChatMessage],
        prompt_manager: Optional[PromptManager] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        チャットメッセージを処理して応答を返す
        
        Args:
            messages: チャットメッセージのリスト
            prompt_manager: プロンプト管理インスタンス（省略時はインスタンス変数を使用）
            temperature: 生成の多様性を制御するパラメータ（0.0-1.0）
            max_tokens: 生成する最大トークン数
            
        Returns:
            str: 生成された応答
            
        Raises:
            PromptNotFoundError: プロンプトが見つからない場合
            APIRequestError: APIリクエストが失敗した場合
            ResponseFormatError: レスポンスの形式が不正な場合
        """
        # プロンプトマネージャーの取得
        pm = prompt_manager or self.prompt_manager
        if not pm:
            raise PromptNotFoundError("chatgpt", "prompt_manager")
        
        # メッセージの変換
        api_messages = []
        for msg in messages:
            if msg.role == "system":
                system_messages = pm.format_messages(
                    provider="chatgpt",
                    template_name="system",
                    content=msg.content
                )
                api_messages.extend(system_messages)
            else:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            # APIリクエストの送信
            response = self.call(
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # レスポンスの検証
            if not response or "content" not in response:
                raise ResponseFormatError("ChatGPT: Empty response from API")
            
            content = response["content"]
            if not content:
                raise ResponseFormatError("ChatGPT: Empty content in response")
            
            return content
            
        except Exception as e:
            raise APIRequestError(f"ChatGPT: API request error: {str(e)}")

# ✅ 構成改善案の生成
def generate_improvement(text: str) -> str:
    """テキストの改善案を生成する"""
    try:
        # メッセージを適切な形式に変換
        messages = [{"role": "user", "content": text}]
        
        # ChatGPT APIを呼び出し
        response = call_chatgpt_api(
            messages=messages,
            model="gpt-4-turbo-preview",
            temperature=0.2
        )
        
        # レスポンスから改善案を取得
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        return "No improvement suggestions available."
    except Exception as e:
        logger.error(f"Error generating improvement: {str(e)}")
        return "Error generating improvement suggestions."

# ✅ 要件要約機能（ステージ summary用）
def summarize_user_requirements(chat_history):
    messages = [{"role": m["role"], "content": m["content"]} for m in chat_history]
    messages.insert(0, {
        "role": "system",
        "content": "以下の会話履歴から、ユーザーが望んでいるアプリの条件・要件を100文字以内で要約してください。"
    })
    return call_chatgpt_api(messages[0]["content"])["content"]

# ✅ コードブロック検出（構成トリガー用）
def contains_code_block(text: str) -> bool:
    """
    コードブロック（```言語名\nコード```）が含まれているかを厳密に判定
    """
    return bool(re.search(r"```(?:\w*\n)?(.+?)```", text, re.DOTALL))

import re

def extract_code_block(text: str) -> str:
    """
    ChatGPTの応答から最初のコードブロック（```～```）を抽出
    """
    match = re.search(r"```(?:\w*\n)?(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_summary_from_chat(chat_history: list) -> str:
    """
    セッション履歴から要約文を生成（最後のassistant応答の冒頭などを仮で使用）
    ※精度が必要なら将来的にLLM要約に置き換え
    """
    for entry in reversed(chat_history):
        if entry["role"] == "assistant":
            lines = entry["content"].strip().splitlines()
            for line in lines:
                if line.strip() and not line.startswith("```"):
                    return line.strip()
    return "No summary available."

def generate_summary(text: str) -> str:
    """テキストの要約を生成する"""
    try:
        # メッセージを適切な形式に変換
        messages = [{"role": "user", "content": text}]
        
        # ChatGPT APIを呼び出し
        response = call_chatgpt_api(
            messages=messages,
            model="gpt-4-turbo-preview",
            temperature=0.2
        )
        
        # レスポンスから要約を取得
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            # 最初の行を取得
            for line in content.split("\n"):
                if line.strip():
                    return line.strip()
        return "No summary available."
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return "Error generating summary."

def call_chatgpt_api(
    messages: List[Dict[str, str]],
    model: str = "gpt-4-turbo-preview",
    temperature: float = 0.5
) -> Dict[str, Any]:
    """
    ChatGPT APIにリクエストを送信し、レスポンスを取得する
    
    Args:
        messages (List[Dict[str, str]]): メッセージのリスト
        model (str, optional): 使用するモデル名. デフォルトは "gpt-4-turbo-preview"
        temperature (float, optional): 生成の多様性を制御するパラメータ. デフォルトは 0.5
        
    Returns:
        Dict[str, Any]: APIレスポンスのJSONデータ
        
    Raises:
        requests.exceptions.RequestException: APIリクエストに失敗した場合
        ValueError: APIキーが設定されていない場合
    """
    # APIキーの取得
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # APIエンドポイント
    url = "https://api.openai.com/v1/chat/completions"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
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
        logger.error(f"ChatGPT API request failed: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ChatGPT API response: {str(e)}")
        raise ValueError(f"Invalid response from ChatGPT API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in ChatGPT API call: {str(e)}")
        raise

def call_chatgpt_evaluation(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    ChatGPTを使用して構成評価を行う
    
    Args:
        messages (List[Dict[str, str]]): 評価用のメッセージリスト
        
    Returns:
        Dict[str, Any]: 評価結果（JSONパース済み）
                      エラー時は空の辞書を返す
    """
    try:
        # メッセージを適切な形式に変換
        formatted_messages = [
            {"role": "user", "content": msg["content"]}
            for msg in messages
        ]
        
        # ChatGPT APIを呼び出し
        response = call_chatgpt_api(
            messages=formatted_messages,
            model="gpt-4-turbo-preview",
            temperature=0.2  # 評価では低めのtemperatureを使用
        )
        
        # レスポンスから評価結果を取得
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            # JSON文字列をパース
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse evaluation result as JSON: {str(e)}")
                return {}
        
        logger.warning("Invalid response format from ChatGPT API")
        return {}
        
    except Exception as e:
        logger.error(f"Error in ChatGPT evaluation: {str(e)}")
        return {}

__all__ = [
    'call_chatgpt_api',
    'call_chatgpt_evaluation'
]
