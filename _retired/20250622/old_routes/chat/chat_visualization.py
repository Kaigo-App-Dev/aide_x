from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
import json
import logging
import os
from datetime import datetime

from src.llm.controller import AIController
from src.llm.providers.chatgpt import ChatGPTProvider
from src.llm.providers.base import ChatMessage
from src.exceptions import AIProviderError, APIRequestError, ResponseFormatError

from src.structure.evaluation import evaluate_with_claude, call_claude_and_gpt
from src.llm.claude import call_claude_api as call_claude
from src.llm.claude import call_claude_evaluation

from src.structure.utils import save_structure, append_structure_log
from src.common.diff import get_diff_highlighted

logger = logging.getLogger(__name__)

def contains_code_block(text: str) -> bool:
    """コードブロックが含まれているかを判定"""
    return "```" in text

def generate_visualization(prompt: str) -> str:
    """可視化の生成"""
    try:
        messages = [ChatMessage(role="user", content=prompt)]
        response = AIController.call(
            provider="chatgpt",
            messages=messages,
            model="gpt-3.5-turbo"
        )
        return response.get("content", "")
    except (APIRequestError, ResponseFormatError) as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating visualization: {str(e)}")
        raise AIProviderError(f"Unexpected error: {str(e)}")

# ... existing code ... 