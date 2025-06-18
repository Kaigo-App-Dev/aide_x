"""
プロンプト関連の型定義

このモジュールは、プロンプト管理に使用される型定義を提供します。
"""

from typing import TypedDict, Optional, List

class MessageParam(TypedDict):
    """メッセージパラメータの型定義"""
    role: str
    content: str
    name: Optional[str]

MessageParamList = List[MessageParam]

class PromptTemplate:
    """プロンプトテンプレートクラス"""
    
    def __init__(self, id: str, provider: str, description: str, template: str):
        """
        初期化
        
        Args:
            id (str): テンプレートの一意識別子
            provider (str): 使用するAIプロバイダー
            description (str): テンプレートの説明
            template (str): プロンプトの内容
        """
        self.id = id
        self.provider = provider
        self.description = description
        self.template = template
    
    def format(self, **kwargs: str) -> str:
        """
        プロンプトをフォーマット
        
        Args:
            **kwargs: フォーマット用のパラメータ
            
        Returns:
            str: フォーマットされたプロンプト
        """
        return self.template.format(**kwargs) 