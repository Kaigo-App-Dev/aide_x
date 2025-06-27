"""XML format handler module for chat functionality."""

from typing import Dict, Any, List, Optional, Union
import xml.etree.ElementTree as ET
import json
import logging

logger = logging.getLogger(__name__)

def process_xml_data(xml_content: str) -> Union[Dict[str, Any], str]:
    """Process XML content and convert it to a structured format.
    
    Args:
        xml_content (str): XML content to process
        
    Returns:
        Union[Dict[str, Any], str]: Processed data in dictionary format or string if the XML
            element only contains text content
        
    Raises:
        ValueError: If XML content is invalid
    """
    try:
        root = ET.fromstring(xml_content)
        return _xml_to_dict(root)
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
        raise ValueError(f"Invalid XML content: {e}")

def validate_xml_format(xml_content: str) -> List[str]:
    """Validate XML format and return any validation errors.
    
    Args:
        xml_content (str): XML content to validate
        
    Returns:
        List[str]: List of validation errors, empty if valid
    """
    errors = []
    try:
        ET.fromstring(xml_content)
    except ET.ParseError as e:
        errors.append(f"XML parsing error: {e}")
    return errors

def _xml_to_dict(element: ET.Element) -> Union[Dict[str, Any], str]:
    """Convert XML element to dictionary or string.
    
    Args:
        element (ET.Element): XML element to convert
        
    Returns:
        Union[Dict[str, Any], str]: Converted dictionary or string
    """
    result = {}
    
    # Add attributes
    for key, value in element.attrib.items():
        result[f"@{key}"] = value
    
    # Add child elements
    for child in element:
        child_data = _xml_to_dict(child)
        if child.tag in result:
            if isinstance(result[child.tag], list):
                result[child.tag].append(child_data)
            else:
                result[child.tag] = [result[child.tag], child_data]
        else:
            result[child.tag] = child_data
    
    # Add text content if present
    if element.text and element.text.strip():
        if result:  # If there are attributes or child elements
            result["#text"] = element.text.strip()
        else:
            return element.text.strip()
    
    return result

def xml_to_json(xml_content: str) -> str:
    """Convert XML content to JSON format.
    
    Args:
        xml_content (str): XML content to convert
        
    Returns:
        str: JSON string representation
        
    Raises:
        ValueError: If XML content is invalid
    """
    try:
        data = process_xml_data(xml_content)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to convert XML to JSON: {e}")
        raise ValueError(f"Failed to convert XML to JSON: {e}")

def json_to_xml(json_content: str) -> str:
    """Convert JSON content to XML format.
    
    Args:
        json_content (str): JSON content to convert
        
    Returns:
        str: XML string representation
        
    Raises:
        ValueError: If JSON content is invalid
    """
    try:
        data = json.loads(json_content)
        root = _dict_to_xml(data)
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        logger.error(f"Failed to convert JSON to XML: {e}")
        raise ValueError(f"Failed to convert JSON to XML: {e}")

def _dict_to_xml(data: Union[Dict[str, Any], Any], root_name: str = "root") -> ET.Element:
    """Convert dictionary or value to XML element.
    
    Args:
        data (Union[Dict[str, Any], Any]): Dictionary or value to convert
        root_name (str): Name for the root element
        
    Returns:
        ET.Element: XML element
    """
    root = ET.Element(root_name)
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key.startswith("@"):
                root.set(key[1:], str(value))
            elif key == "#text":
                root.text = str(value)
            elif isinstance(value, list):
                for item in value:
                    child = _dict_to_xml(item, key)
                    root.append(child)
            else:
                child = _dict_to_xml(value, key)
                root.append(child)
    else:
        root.text = str(data)
    
    return root 