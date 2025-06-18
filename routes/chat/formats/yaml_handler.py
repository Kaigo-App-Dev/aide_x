"""YAML format handler module for chat functionality."""

from typing import Dict, Any, List, Optional, Union
import yaml
import json
import logging

logger = logging.getLogger(__name__)

def process_yaml_data(yaml_content: str) -> Union[Dict[str, Any], List[Any], str, int, float, bool, None]:
    """Process YAML content and convert it to a structured format.
    
    Args:
        yaml_content (str): YAML content to process
        
    Returns:
        Union[Dict[str, Any], List[Any], str, int, float, bool, None]: Processed data
        
    Raises:
        ValueError: If YAML content is invalid
    """
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
        raise ValueError(f"Invalid YAML content: {e}")

def validate_yaml_format(yaml_content: str) -> List[str]:
    """Validate YAML format and return any validation errors.
    
    Args:
        yaml_content (str): YAML content to validate
        
    Returns:
        List[str]: List of validation errors, empty if valid
    """
    errors = []
    try:
        yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        errors.append(f"YAML parsing error: {e}")
    return errors

def yaml_to_json(yaml_content: str) -> str:
    """Convert YAML content to JSON format.
    
    Args:
        yaml_content (str): YAML content to convert
        
    Returns:
        str: JSON string representation
        
    Raises:
        ValueError: If YAML content is invalid
    """
    try:
        data = process_yaml_data(yaml_content)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to convert YAML to JSON: {e}")
        raise ValueError(f"Failed to convert YAML to JSON: {e}")

def json_to_yaml(json_content: str) -> str:
    """Convert JSON content to YAML format.
    
    Args:
        json_content (str): JSON content to convert
        
    Returns:
        str: YAML string representation
        
    Raises:
        ValueError: If JSON content is invalid
    """
    try:
        data = json.loads(json_content)
        return yaml.dump(data, allow_unicode=True, sort_keys=False)
    except Exception as e:
        logger.error(f"Failed to convert JSON to YAML: {e}")
        raise ValueError(f"Failed to convert JSON to YAML: {e}")

def merge_yaml_files(yaml_contents: List[str]) -> str:
    """Merge multiple YAML files into a single YAML.
    
    Args:
        yaml_contents (List[str]): List of YAML contents to merge
        
    Returns:
        str: Merged YAML content
        
    Raises:
        ValueError: If any YAML content is invalid
    """
    try:
        merged_data = {}
        for content in yaml_contents:
            data = process_yaml_data(content)
            if isinstance(data, dict):
                merged_data.update(data)
            else:
                logger.warning(f"Skipping non-dict YAML content: {type(data)}")
        return yaml.dump(merged_data, allow_unicode=True, sort_keys=False)
    except Exception as e:
        logger.error(f"Failed to merge YAML files: {e}")
        raise ValueError(f"Failed to merge YAML files: {e}")

def extract_yaml_section(yaml_content: str, section_path: str) -> Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]]:
    """Extract a specific section from YAML content.
    
    Args:
        yaml_content (str): YAML content to process
        section_path (str): Dot-separated path to the section
        
    Returns:
        Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]]: Extracted section or None if not found
        
    Raises:
        ValueError: If YAML content is invalid
    """
    try:
        data = process_yaml_data(yaml_content)
        current = data
        for key in section_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    except Exception as e:
        logger.error(f"Failed to extract YAML section: {e}")
        raise ValueError(f"Failed to extract YAML section: {e}") 