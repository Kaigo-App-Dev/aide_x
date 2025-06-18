"""Logging utilities for the application."""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

def save_log(
    message: str,
    level: int = logging.INFO,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Save a log message with the specified level and extra information.
    
    Args:
        message: The log message to save.
        level: The logging level (default: logging.INFO).
        extra: Additional information to include in the log (default: None).
    """
    logger = logging.getLogger(__name__)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Add handler if not already added
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    # Log the message
    logger.log(level, message, extra=extra) 