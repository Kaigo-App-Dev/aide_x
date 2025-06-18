from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
import json
import logging
import os
from datetime import datetime

from src.llm.controller import AIController
from src.llm.providers.claude import ClaudeProvider
from src.llm.providers.base import ChatMessage
from src.common.exceptions import AIProviderError, APIRequestError, ResponseFormatError

from src.structure.utils import save_structure, append_structure_log

logger = logging.getLogger(__name__)

def evaluate_workflow(prompt: str) -> str:
    """ワークフローの評価"""
    try:
        messages = [ChatMessage(role="user", content=prompt)]
        response = AIController.call(
            provider="claude",
            messages=messages,
            model="claude-3-sonnet-20240229"
        )
        return response.get("content", "")
    except (APIRequestError, ResponseFormatError) as e:
        logger.error(f"Error evaluating workflow: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error evaluating workflow: {str(e)}")
        raise AIProviderError(f"Unexpected error: {str(e)}")

def generate_workflow(prompt: str) -> str:
    """ワークフローの生成"""
    try:
        messages = [ChatMessage(role="user", content=prompt)]
        response = AIController.call(
            provider="claude",
            messages=messages,
            model="claude-3-sonnet-20240229"
        )
        return response.get("content", "")
    except (APIRequestError, ResponseFormatError) as e:
        logger.error(f"Error generating workflow: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating workflow: {str(e)}")
        raise AIProviderError(f"Unexpected error: {str(e)}")

# ... existing code ... 