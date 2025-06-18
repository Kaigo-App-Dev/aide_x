"""
プロンプトテンプレートのYAMLファイルからの読み込みを担当するモジュール
"""

import yaml
import logging
from typing import List
from pathlib import Path
from .manager import PromptManager, Prompt

logger = logging.getLogger(__name__)

def load_prompts_from_yaml(file_path: str) -> List[Prompt]:
    """
    YAMLファイルからプロンプトテンプレートを読み込む

    Args:
        file_path (str): YAMLファイルのパス

    Returns:
        List[Prompt]: 読み込まれたプロンプトのリスト

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        yaml.YAMLError: YAMLの解析に失敗した場合
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        prompts = []
        for item in data:
            prompt = Prompt(
                name=item['name'],
                provider=item['provider'],
                description=item['description'],
                template=item['template']
            )
            prompts.append(prompt)
            logger.debug(f"Loaded prompt template: {prompt.name} for provider {prompt.provider}")
        
        return prompts
    except FileNotFoundError:
        logger.error(f"Prompt template file not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {file_path}: {str(e)}")
        raise

def register_from_yaml(file_path: str, manager: PromptManager) -> None:
    """
    YAMLファイルからプロンプトテンプレートを読み込み、PromptManagerに登録する

    Args:
        file_path (str): YAMLファイルのパス
        manager (PromptManager): プロンプトマネージャーインスタンス

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        yaml.YAMLError: YAMLの解析に失敗した場合
    """
    prompts = load_prompts_from_yaml(file_path)
    for prompt in prompts:
        manager.register(prompt)
        logger.info(f"Registered template: {prompt.name} for provider {prompt.provider}")

def register_all_yaml_templates(manager: PromptManager) -> None:
    """
    プロンプトテンプレートディレクトリ内のすべてのYAMLファイルを読み込み、登録する

    Args:
        manager (PromptManager): プロンプトマネージャーインスタンス
    """
    yaml_dir = Path(__file__).parent / 'yaml'
    if not yaml_dir.exists():
        logger.warning(f"Prompt templates directory not found: {yaml_dir}")
        return

    for yaml_file in yaml_dir.glob('*.yaml'):
        try:
            register_from_yaml(str(yaml_file), manager)
        except Exception as e:
            logger.error(f"Failed to register templates from {yaml_file}: {str(e)}") 