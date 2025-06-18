"""
Prompt Class

プロンプトテンプレートを表現するクラスを提供します。
"""

from typing import Optional, Dict, Any

class Prompt:
    """プロンプトテンプレートを表現するクラス"""
    
    def __init__(self, template: str, description: str = ""):
        """
        プロンプトテンプレートを初期化
        
        Args:
            template (str): プロンプトテンプレート
            description (str, optional): プロンプトの説明. Defaults to "".
        """
        self.template = template
        self.description = description
    
    def format(self, **kwargs: Any) -> str:
        """
        テンプレートに値を埋め込む
        
        Args:
            **kwargs: テンプレートに埋め込む値
            
        Returns:
            str: 埋め込まれたテンプレート
        """
        return self.template.format(**kwargs)
    
    def __repr__(self) -> str:
        """文字列表現を返す"""
        return f"Prompt(template='{self.template[:30]}...', description='{self.description[:30]}...')" 