"""
Prompt Class

プロンプトテンプレートを表現するクラスを提供します。
"""

from typing import Optional, Dict, Any, List
from .types import MessageParam

class Prompt:
    """プロンプトテンプレートを表現するクラス"""
    
    def __init__(self, template: str, description: str = "", messages: Optional[List[MessageParam]] = None):
        """
        プロンプトテンプレートを初期化
        
        Args:
            template (str): プロンプトテンプレート
            description (str, optional): プロンプトの説明. Defaults to "".
            messages (Optional[List[MessageParam]], optional): メッセージリスト. Defaults to None.
        """
        self.template = template
        self.description = description
        self.messages = messages or []
    
    def format(self, **kwargs: Any) -> str:
        """
        テンプレートに値を埋め込む
        
        Args:
            **kwargs: テンプレートに埋め込む値
            
        Returns:
            str: 埋め込まれたテンプレート
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template parameter: {e}")
        except Exception as e:
            raise ValueError(f"Failed to format template: {e}")
    
    def __repr__(self) -> str:
        """文字列表現を返す"""
        return f"Prompt(template='{self.template[:30]}...', description='{self.description[:30]}...')" 