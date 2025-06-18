"""
ChatGPT AIプロバイダー

このモジュールは、OpenAIのChatGPTモデルを使用するためのプロバイダーを提供します。
"""

import logging
import openai
from openai.types.chat import ChatCompletion
from src.llm.providers.base import BaseLLMProvider, ChatMessage
from src.llm.providers.types import AIProviderResponse
from src.common.exceptions import ChatGPTAPIError, PromptNotFoundError, ResponseFormatError
from src.common.logging_utils import save_log
from src.llm.prompts.manager import PromptManager
import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import re
import yaml
import requests
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
        dump_path = f"logs/chatgpt_error_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(error_dump, f, ensure_ascii=False, indent=2)
        logger.error(f"JSON extraction failed: {e}")
        return {}

class ChatGPTProvider:
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
