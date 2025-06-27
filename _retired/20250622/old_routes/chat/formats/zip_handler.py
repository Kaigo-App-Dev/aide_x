"""ZIP format handler module for chat functionality."""

from typing import Dict, Any, List, Optional, Union, BinaryIO
import zipfile
import io
import json
import yaml
import xml.etree.ElementTree as ET
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def process_zip_data(zip_content: bytes) -> Dict[str, bytes]:
    """Process ZIP content and extract its contents.
    
    Args:
        zip_content (bytes): ZIP file content
        
    Returns:
        Dict[str, bytes]: Dictionary containing extracted files and their contents
        
    Raises:
        ValueError: If ZIP content is invalid
    """
    try:
        result = {}
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            for file_info in zip_file.filelist:
                if not file_info.is_dir():
                    content = zip_file.read(file_info.filename)
                    result[file_info.filename] = content
        return result
    except zipfile.BadZipFile as e:
        logger.error(f"Failed to process ZIP: {e}")
        raise ValueError(f"Invalid ZIP content: {e}")

def validate_zip_format(zip_content: bytes) -> List[str]:
    """Validate ZIP format and return any validation errors.
    
    Args:
        zip_content (bytes): ZIP content to validate
        
    Returns:
        List[str]: List of validation errors, empty if valid
    """
    errors = []
    try:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            # Test if ZIP file is valid
            zip_file.testzip()
    except zipfile.BadZipFile as e:
        errors.append(f"ZIP parsing error: {e}")
    return errors

def create_zip_from_files(files: Dict[str, Union[Dict[str, Any], List[Any], str, bytes]]) -> bytes:
    """Create a ZIP file from a dictionary of files.
    
    Args:
        files (Dict[str, Union[Dict[str, Any], List[Any], str, bytes]]): Dictionary mapping filenames to content
        
    Returns:
        bytes: ZIP file content
        
    Raises:
        ValueError: If file content is invalid
    """
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in files.items():
                if isinstance(content, (dict, list)):
                    content = json.dumps(content, ensure_ascii=False)
                elif not isinstance(content, (str, bytes)):
                    content = str(content)
                if isinstance(content, str):
                    content = content.encode('utf-8')
                zip_file.writestr(filename, content)
        return zip_buffer.getvalue()
    except Exception as e:
        logger.error(f"Failed to create ZIP: {e}")
        raise ValueError(f"Failed to create ZIP: {e}")

def extract_zip_to_files(zip_content: bytes, target_dir: str) -> List[str]:
    """Extract ZIP contents to files in a target directory.
    
    Args:
        zip_content (bytes): ZIP file content
        target_dir (str): Target directory path
        
    Returns:
        List[str]: List of extracted file paths
        
    Raises:
        ValueError: If ZIP content is invalid or extraction fails
    """
    try:
        extracted_files = []
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            for file_info in zip_file.filelist:
                if not file_info.is_dir():
                    file_path = target_path / file_info.filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'wb') as f:
                        f.write(zip_file.read(file_info.filename))
                    extracted_files.append(str(file_path))
        return extracted_files
    except Exception as e:
        logger.error(f"Failed to extract ZIP: {e}")
        raise ValueError(f"Failed to extract ZIP: {e}")

def merge_zip_files(zip_contents: List[bytes]) -> bytes:
    """Merge multiple ZIP files into a single ZIP.
    
    Args:
        zip_contents (List[bytes]): List of ZIP file contents
        
    Returns:
        bytes: Merged ZIP file content
        
    Raises:
        ValueError: If any ZIP content is invalid
    """
    try:
        merged_files = {}
        for zip_content in zip_contents:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
                for file_info in zip_file.filelist:
                    if not file_info.is_dir():
                        content = zip_file.read(file_info.filename)
                        if file_info.filename in merged_files:
                            logger.warning(f"Duplicate file found: {file_info.filename}")
                        merged_files[file_info.filename] = content
        return create_zip_from_files(merged_files)
    except Exception as e:
        logger.error(f"Failed to merge ZIP files: {e}")
        raise ValueError(f"Failed to merge ZIP files: {e}")

def extract_zip_file(zip_content: bytes, filename: str) -> Optional[bytes]:
    """Extract a specific file from ZIP content.
    
    Args:
        zip_content (bytes): ZIP file content
        filename (str): Name of the file to extract
        
    Returns:
        Optional[bytes]: Extracted file content or None if not found
        
    Raises:
        ValueError: If ZIP content is invalid
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            if filename in zip_file.namelist():
                return zip_file.read(filename)
            return None
    except Exception as e:
        logger.error(f"Failed to extract file from ZIP: {e}")
        raise ValueError(f"Failed to extract file from ZIP: {e}") 