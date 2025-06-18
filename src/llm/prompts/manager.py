"""
プロンプト管理

このモジュールは、AIプロバイダー用のプロンプトテンプレートを管理します。
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from src.exceptions import PromptNotFoundError, TemplateFormatError

logger = logging.getLogger(__name__)

@dataclass
class Prompt:
    """プロンプトテンプレート"""
    name: str
    provider: str
    description: str
    template: str

class PromptManager:
    """プロンプト管理クラス"""
    
    def __init__(self):
        """PromptManagerの初期化"""
        self.templates: Dict[str, Dict[str, str]] = {}
        logger.info("PromptManager initialized")
    
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
            
            # テンプレートのフォーマットを検証
            template.format(placeholder="test")
            
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
            TemplateFormatError: テンプレートのフォーマットが不正な場合
        """
        template = self.get_template(provider, template_name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            error_msg = f"Missing required placeholder: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(provider, template_name, error_msg)
        except Exception as e:
            error_msg = f"Failed to format template: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(provider, template_name, error_msg)

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
    
    def get_prompt(self, provider: str, name: str) -> Optional[Prompt]:
        """
        プロンプトテンプレートを取得

        Args:
            provider (str): プロバイダー名
            name (str): テンプレート名

        Returns:
            Optional[Prompt]: プロンプトテンプレート（存在しない場合はNone）
        """
        try:
            prompt = self.templates[provider][name]
            logger.debug(f"Retrieved prompt: {name} for provider {provider}")
            return Prompt(name, provider, "", prompt)
        except KeyError:
            logger.error(f"Prompt not found: {name} for provider {provider}")
            return None 