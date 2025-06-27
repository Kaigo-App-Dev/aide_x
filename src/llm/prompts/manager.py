"""
プロンプト管理

このモジュールは、AIプロバイダー用のプロンプトテンプレートを管理します。
"""

import logging
from typing import Dict, Optional, Any, List, Union
from dataclasses import dataclass
from src.exceptions import PromptNotFoundError, TemplateFormatError
from src.types import MessageParam, MessageParamList

logger = logging.getLogger(__name__)

@dataclass
class Prompt:
    """プロンプトテンプレート"""
    name: str
    provider: str
    description: str
    template: str
    messages: Optional[List[MessageParam]] = None

    def render(self, content: str) -> str:
        """
        テンプレートをレンダリング
        
        Args:
            content: テンプレートに埋め込む内容
            
        Returns:
            str: レンダリングされたテンプレート
        """
        try:
            return self.template.format(content=content)
        except KeyError as e:
            error_msg = f"Invalid template format: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(self.provider, self.name, error_msg)
        except Exception as e:
            error_msg = f"Failed to render template: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(self.provider, self.name, error_msg)

    def format(self, **kwargs) -> str:
        """
        テンプレートをフォーマット
        
        Args:
            **kwargs: テンプレートのプレースホルダーに渡す値
            
        Returns:
            str: フォーマットされたテンプレート
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            error_msg = f"Invalid template format: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(self.provider, self.name, error_msg)
        except Exception as e:
            error_msg = f"Failed to format template: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(self.provider, self.name, error_msg)

class PromptAlreadyExistsError(Exception):
    """テンプレート重複登録時の例外"""
    def __init__(self, provider: str, template_name: str):
        super().__init__(f"Template '{template_name}' already exists for provider '{provider}'")
        self.provider = provider
        self.template_name = template_name

class PromptManager:
    """プロンプト管理クラス"""
    
    def __init__(self):
        """PromptManagerの初期化"""
        self.templates: Dict[str, Dict[str, str]] = {}
        self.builtin_templates: Dict[str, str] = {}
        self.prompts: Dict[str, Prompt] = {}
        logger.info("PromptManager initialized")
        
        # テンプレートを自動登録
        try:
            from .templates import register_all_templates
            register_all_templates(self)
            logger.info("✅ テンプレート自動登録完了")
        except Exception as e:
            logger.warning(f"⚠️ テンプレート自動登録に失敗: {str(e)}")
    
    def register_template(self, provider: str, template_name: str, template: str, description: str = "") -> None:
        """
        テンプレートを登録
        
        Args:
            provider (str): プロバイダー名
            template_name (str): テンプレート名
            template (str): テンプレート文字列
            description (str): テンプレートの説明
            
        Raises:
            TemplateFormatError: テンプレートのフォーマットが不正な場合
        """
        try:
            if provider not in self.templates:
                self.templates[provider] = {}
            if template_name in self.templates[provider]:
                raise PromptAlreadyExistsError(provider, template_name)
            
            # テンプレートのフォーマットを検証
            # template.format(placeholder="test")  # 検証無効化 - プレースホルダー名が不明なため
            
            self.templates[provider][template_name] = template
            logger.info(f"Template '{template_name}' registered for provider '{provider}'")
        except KeyError as e:
            error_msg = f"Invalid template format: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(provider, template_name, error_msg)
        except Exception as e:
            error_msg = f"Failed to register template: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(provider, template_name, error_msg)
    
    def get_template(self, provider: str, template_name: str) -> Optional[str]:
        """
        テンプレートを取得
        
        Args:
            provider (str): プロバイダー名
            template_name (str): テンプレート名
            
        Returns:
            Optional[str]: テンプレート文字列、存在しない場合はNone
            
        Raises:
            PromptNotFoundError: テンプレートが見つからない場合
        """
        try:
            if provider not in self.templates:
                raise PromptNotFoundError(provider, template_name)
            
            template = self.templates[provider].get(template_name)
            if not template:
                raise PromptNotFoundError(provider, template_name)
            
            return template
        except PromptNotFoundError:
            logger.error(f"Template '{template_name}' not found for provider '{provider}'")
            raise
        except Exception as e:
            error_msg = f"Failed to get template: {str(e)}"
            logger.error(error_msg)
            raise PromptNotFoundError(provider, template_name)
    
    def format_template(self, provider: str, template_name: str, **kwargs) -> str:
        """
        テンプレートをフォーマット
        
        Args:
            provider (str): プロバイダー名
            template_name (str): テンプレート名
            **kwargs: テンプレートのプレースホルダーに渡す値
            
        Returns:
            str: フォーマットされたテンプレート
            
        Raises:
            PromptNotFoundError: テンプレートが見つからない場合
        """
        prompt_name = f"{provider}.{template_name}"
        prompt = self.prompts.get(prompt_name)
        if not prompt:
            raise PromptNotFoundError(provider, template_name)
        
        try:
            return prompt.template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Template formatting error: {str(e)}")
            raise PromptNotFoundError(provider, template_name)

    def register(self, prompt: Prompt) -> None:
        """
        プロンプトテンプレートを登録

        Args:
            prompt (Prompt): 登録するプロンプトテンプレート
        """
        if prompt.provider not in self.templates:
            self.templates[prompt.provider] = {}
            logger.debug(f"Created new provider entry: {prompt.provider}")
        
        self.templates[prompt.provider][prompt.name] = prompt.template
        logger.debug(f"Registered template: {prompt.name} for provider {prompt.provider}")
        
        prompt_name = f"{prompt.provider}.{prompt.name}"
        self.prompts[prompt_name] = prompt
    
    def get_prompt(self, provider: str, template_name: str) -> Optional[Prompt]:
        """
        プロンプトテンプレートを取得

        Args:
            provider (str): プロバイダー名
            template_name (str): テンプレート名

        Returns:
            Optional[Prompt]: プロンプトテンプレート（存在しない場合はNone）
        """
        prompt_name = f"{provider}.{template_name}"
        logger.info(f"🔍 get_prompt - provider: {provider}, template_name: {template_name}")
        logger.info(f"🔍 get_prompt - prompt_name: {prompt_name}")
        logger.info(f"🔍 get_prompt - available keys: {list(self.prompts.keys())}")
        
        result = self.prompts.get(prompt_name)
        if result:
            logger.info(f"✅ get_prompt - found: {prompt_name}")
        else:
            logger.warning(f"❌ get_prompt - not found: {prompt_name}")
        
        return result

    def get(self, template_name: str) -> Union[str, Dict[str, str]]:
        """
        テンプレートを取得
        
        Args:
            template_name: テンプレート名
            
        Returns:
            Union[str, Dict[str, str]]: テンプレート内容
            
        Raises:
            PromptNotFoundError: テンプレートが見つからない場合
        """
        if template_name in self.templates:
            return self.templates[template_name]
        if template_name in self.builtin_templates:
            return self.builtin_templates[template_name]
        raise PromptNotFoundError("", template_name)
    
    def register_builtin_templates(self) -> None:
        """組み込みテンプレートを登録する（非推奨 - __init__.pyで自動登録）"""
        logger.warning("register_builtin_templates is deprecated. Templates are automatically registered in __init__.py")
        pass
    
    def format_prompt(self, template_name: str, **kwargs: Any) -> str:
        """
        プロンプトをフォーマット
        
        Args:
            template_name: テンプレート名
            **kwargs: フォーマット用の引数
            
        Returns:
            str: フォーマットされたプロンプト
        """
        template = self.get(template_name)
        if isinstance(template, dict):
            raise ValueError(f"Template '{template_name}' is a dictionary, not a string")
        return template.format(**kwargs)
    
    def format_messages(self, provider: str, template_name: str, **kwargs) -> MessageParamList:
        """
        メッセージリストをフォーマット
        
        Args:
            provider (str): プロバイダー名
            template_name (str): テンプレート名
            **kwargs: フォーマット用の引数
            
        Returns:
            MessageParamList: フォーマットされたメッセージリスト
        """
        prompt_name = f"{provider}.{template_name}"
        prompt = self.get_prompt(provider, template_name)
        if not prompt:
            raise PromptNotFoundError(provider, template_name)

        try:
            messages = []
            if prompt.messages:
                for msg in prompt.messages:
                    formatted_content = msg["content"].format(**kwargs)
                    messages.append({
                        "role": msg["role"],
                        "content": formatted_content,
                        "name": msg.get("name", "")
                    })
            else:
                # メッセージリストがない場合は、テンプレートをユーザーメッセージとして使用
                formatted_content = prompt.template.format(**kwargs)
                messages.append({
                    "role": "user",
                    "content": formatted_content,
                    "name": ""
                })
            return messages
        except KeyError as e:
            logger.error(f"Message formatting error: {str(e)}")
            raise PromptNotFoundError(provider, template_name)

# シングルトンインスタンス
prompt_manager = PromptManager()

# グローバルインスタンスにテンプレートを登録
try:
    from .templates import register_all_templates
    register_all_templates(prompt_manager)
    from .prompt_loader import register_all_yaml_templates
    register_all_yaml_templates(prompt_manager)
    logger.info("Global PromptManager initialized with templates")
except Exception as e:
    logger.warning(f"Failed to register templates to global PromptManager: {str(e)}") 