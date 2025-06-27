"""
Gemini AIプロバイダー

このモジュールは、GoogleのGeminiモデルを使用するためのプロバイダーを提供します。
"""

import logging
from google import generativeai as genai
from src.llm.providers.base import BaseLLMProvider, ChatMessage
from src.llm.providers.types import AIProviderResponse
from src.exceptions import GeminiAPIError, PromptNotFoundError, ResponseFormatError, APIRequestError
from src.utils.logging import save_log
from src.llm.prompts.manager import PromptManager
from src.llm.prompts.prompt import Prompt
from src.structure_feedback_engine import StructureFeedbackEngine
import os
import json
import requests
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import yaml
from src.exceptions import ProviderInitializationError, APIKeyMissingError
from copy import deepcopy

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
    """
    未クオートのJSONキーを修正する
    
    Args:
        json_str (str): 修正対象のJSON文字列
        
    Returns:
        str: 修正後のJSON文字列
    """
    # 文字列リテラル内のコロンを保護
    protected_str = re.sub(r'"[^"]*"', lambda m: m.group(0).replace(':', '\\u003A'), json_str)
    
    # 未クオートのキーを検出して修正
    # 1. オブジェクトの開始（{）またはカンマ（,）の後に続く
    # 2. 任意の空白文字
    # 3. 有効なキー名（英数字、アンダースコア、ハイフン）
    # 4. 任意の空白文字
    # 5. コロン（:）
    pattern = r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:'
    
    # キーをクオートで囲む
    fixed = re.sub(pattern, r'\1"\2":', protected_str)
    
    # 保護した文字列リテラルを元に戻す
    fixed = fixed.replace('\\u003A', ':')
    
    return fixed

def extract_json_part(text: str) -> Dict[str, Any]:
    """
    テキストからJSON部分を抽出して解析する（src/utils/files.pyのextract_json_partを使用）
    
    Args:
        text (str): 入力テキスト
        
    Returns:
        Dict[str, Any]: 抽出されたJSON、失敗時はエラー情報を含む辞書
    """
    try:
        # src/utils/files.pyのextract_json_partを使用
        from src.utils.files import extract_json_part as files_extract_json_part
        return files_extract_json_part(text)
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
        return {
            "error": "JSON抽出に失敗しました",
            "reason": str(e),
            "original_text": text[:200] + "..." if len(text) > 200 else text
        }

class GeminiProvider(BaseLLMProvider):
    """Gemini AIプロバイダークラス"""
    
    def __init__(self, prompt_manager: PromptManager, api_key: Optional[str] = None):
        """
        GeminiProviderの初期化
        
        Args:
            prompt_manager (PromptManager): プロンプト管理インスタンス（必須）
            api_key (Optional[str]): Google APIキー（環境変数GEMINI_API_KEYからも取得可能）
            
        Raises:
            ProviderInitializationError: prompt_managerが指定されていない場合
            APIKeyMissingError: APIキーが見つからない場合
        """
        if prompt_manager is None:
            error_msg = "PromptManager instance is required"
            logger.error(error_msg)
            raise ProviderInitializationError("gemini", error_msg)
        self.prompt_manager = prompt_manager
        
        # APIキーの取得（優先順位: 引数 > GEMINI_API_KEY > GOOGLE_API_KEY）
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        # APIキーの詳細ログ
        logger.debug(f"🔑 Gemini APIキー確認:")
        logger.debug(f"  - 引数指定: {'あり' if api_key else 'なし'}")
        logger.debug(f"  - GEMINI_API_KEY: {'設定済み' if os.getenv('GEMINI_API_KEY') else '未設定'}")
        logger.debug(f"  - GOOGLE_API_KEY: {'設定済み' if os.getenv('GOOGLE_API_KEY') else '未設定'}")
        logger.debug(f"  - 最終使用キー: {'設定済み' if self.api_key else '未設定'}")
        
        if not self.api_key:
            error_msg = "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is not set"
            logger.error(error_msg)
            raise APIKeyMissingError("gemini", ["GEMINI_API_KEY", "GOOGLE_API_KEY"])
        
        try:
            # Call parent constructor first
            super().__init__(model="gemini-1.5-flash")
            
            # Gemini APIの設定
            genai.configure(api_key=self.api_key)
            self.model_name = "gemini-1.5-flash"
            # Set the actual model instance after parent constructor
            self.model = genai.GenerativeModel(self.model_name)
            self.feedback_engine = StructureFeedbackEngine()
            logger.info("✅ GeminiProvider initialized with PromptManager and API Key")
            logger.debug(f"🎯 使用モデル: {self.model_name}")
        except Exception as e:
            error_msg = f"Failed to initialize Gemini model: {str(e)}"
            logger.error(error_msg)
            raise ProviderInitializationError("gemini", error_msg)
    
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
            logger.debug(f"🎯 Gemini generate_response開始")
            logger.debug(f"📝 プロンプト: {prompt[:200]}...")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", 0.7),
                    max_output_tokens=kwargs.get("max_tokens", 1024)
                )
            )
            
            if not response or not getattr(response, "text", None):
                error_msg = "Gemini: Response format error - response is None or has no text"
                logger.error(error_msg)
                raise ResponseFormatError(error_msg)
            
            response_text = response.text
            logger.debug(f"✅ Gemini generate_response成功 - 文字数: {len(response_text)}")
            
            return response_text
            
        except Exception as e:
            error_msg = f"Gemini: generate_response error: {str(e)}"
            logger.error(error_msg)
            raise ResponseFormatError(error_msg)
    
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
                    "model": self.model_name,
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
                    # JSON部分を抽出
                    extracted_json = extract_json_part(content)
                    if not extracted_json:
                        raise ResponseFormatError("Gemini: Failed to extract valid JSON from response.")
                    
                    # 構造フィードバックエンジンを使用してJSONを処理
                    reference_json = kwargs.get("reference_json")
                    if reference_json:
                        result = self.feedback_engine.process_structure(
                            json.dumps(extracted_json),
                            reference_json
                        )
                    else:
                        result = extracted_json
                    
                    # レスポンスログの保存
                    save_log(
                        "Gemini API response",
                        logging.INFO,
                        {
                            "model": self.model_name,
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
                except Exception as e:
                    raise ResponseFormatError(f"Gemini: Failed to process JSON response: {str(e)}")
            
            # 通常レスポンスのログ保存
            save_log(
                "Gemini API response",
                logging.INFO,
                {
                    "model": self.model_name,
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
                    "model": self.model_name,
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
                    "model": self.model_name,
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

    def chat(self, prompt: 'Prompt', model_name: str, prompt_manager: 'PromptManager', **kwargs) -> str:
        """
        Gemini用の統一chatインターフェース
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
            
            # 詳細なリクエストログを出力
            logger.info(f"🎯 Gemini補完開始 - model: {model_name}")
            logger.info(f"📝 Geminiプロンプト全文:")
            logger.info(f"{'='*50}")
            logger.info(f"{prompt_str}")
            logger.info(f"{'='*50}")
            
            # APIキーの確認
            api_key = os.getenv("GEMINI_API_KEY")
            logger.info(f"🔐 APIキー確認: {'設定済み' if api_key else '未設定'}")
            if api_key:
                logger.debug(f"🔑 APIキー長: {len(api_key)}文字")
            else:
                raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
            
            save_log(
                "Gemini API request",
                logging.INFO,
                {
                    "model": model_name,
                    "prompt": prompt_str,
                    "prompt_length": len(prompt_str),
                    "kwargs": kwargs,
                    "api_key_set": bool(api_key)
                }
            )
            
            # APIリクエストの詳細ログ
            logger.info(f"🔗 Gemini API呼び出し:")
            logger.info(f"  - モデル: {model_name}")
            logger.info(f"  - プロンプト長: {len(prompt_str)}")
            logger.info(f"  - パラメータ: {kwargs}")
            logger.info("📡 Gemini API送信中...")
            
            response = self.model.generate_content(
                prompt_str,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", 0.7),
                    max_output_tokens=kwargs.get("max_tokens", 1024)
                )
            )
            
            # レスポンスの詳細ログ
            logger.info("✅ Gemini API送信完了")
            logger.debug(f"📡 Gemini APIレスポンス:")
            logger.debug(f"  - レスポンス型: {type(response)}")
            logger.debug(f"  - レスポンス内容: {str(response)[:200]}...")
            
            if not response or not getattr(response, "text", None):
                error_msg = "Gemini: Response format error - response is None or has no text"
                logger.error(error_msg)
                logger.error(f"❌ レスポンス詳細: {str(response)}")
                save_log(
                    "Gemini API error",
                    logging.ERROR,
                    {
                        "model": model_name,
                        "error": error_msg,
                        "response": str(response) if response else "None",
                        "response_type": str(type(response))
                    }
                )
                raise ResponseFormatError(error_msg)
            
            response_text = response.text
            logger.info(f"✅ Gemini応答取得成功 - 文字数: {len(response_text)}")
            logger.debug(f"📄 Gemini生出力:")
            logger.debug(f"{'='*50}")
            logger.debug(f"{response_text}")
            logger.debug(f"{'='*50}")
            
            save_log(
                "Gemini API response",
                logging.INFO,
                {
                    "model": model_name,
                    "result": response_text,
                    "result_length": len(response_text),
                    "raw_response": str(response)
                }
            )
            
            return response_text
            
        except ResponseFormatError as e:
            error_msg = f"Gemini: Response format error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"❌ エラー詳細: {str(e)}")
            save_log(
                "Gemini API error",
                logging.ERROR,
                {
                    "model": model_name,
                    "error": error_msg,
                    "prompt": prompt_str if 'prompt_str' in locals() else "Unknown",
                    "error_type": "ResponseFormatError"
                }
            )
            # 例外を再発生させるが、Noneは返さない
            raise
        except requests.RequestException as e:
            error_msg = f"Gemini: Network request error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"❌ ネットワークエラー詳細: {str(e)}")
            logger.error(f"❌ 例外型: {type(e).__name__}")
            save_log(
                "Gemini API error",
                logging.ERROR,
                {
                    "model": model_name,
                    "error": error_msg,
                    "prompt": prompt_str if 'prompt_str' in locals() else "Unknown",
                    "error_type": "RequestException",
                    "error_details": str(e)
                }
            )
            raise APIRequestError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Gemini: JSON decode error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"❌ JSONデコードエラー詳細: {str(e)}")
            logger.error(f"❌ 例外型: {type(e).__name__}")
            save_log(
                "Gemini API error",
                logging.ERROR,
                {
                    "model": model_name,
                    "error": error_msg,
                    "prompt": prompt_str if 'prompt_str' in locals() else "Unknown",
                    "error_type": "JSONDecodeError",
                    "error_details": str(e)
                }
            )
            raise ResponseFormatError(error_msg)
        except Exception as e:
            error_msg = f"Gemini: API request error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"❌ 例外詳細: {str(e)}")
            logger.error(f"❌ 例外型: {type(e).__name__}")
            import traceback
            logger.error(f"❌ スタックトレース: {traceback.format_exc()}")
            save_log(
                "Gemini API error",
                logging.ERROR,
                {
                    "model": model_name,
                    "error": error_msg,
                    "prompt": prompt_str if 'prompt_str' in locals() else "Unknown",
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                    "stack_trace": traceback.format_exc()
                }
            )
            # 例外を再発生させるが、Noneは返さない
            raise APIRequestError(error_msg)

def call_gemini_api(
    messages: List[Dict[str, str]],
    model: str = "gemini-1.5-flash",
    temperature: float = 0.8
) -> str:
    """
    Gemini APIにリクエストを送信し、レスポンスを取得する
    
    Args:
        messages (List[Dict[str, str]]): メッセージのリスト
        model (str, optional): 使用するモデル名. デフォルトは "gemini-1.5-flash"
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