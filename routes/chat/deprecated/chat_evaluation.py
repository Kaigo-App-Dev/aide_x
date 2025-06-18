from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
import json
import logging
import os
from datetime import datetime

from src.llm.hub import safe_generate_and_evaluate

from src.llm.evaluation import evaluate_with_claude, call_claude_and_gpt
from src.llm.claude import call_claude_api as call_claude
from src.llm.claude import call_claude_evaluation

from src.structure.utils import save_structure, append_structure_log
from src.common.diff import get_diff_highlighted

# ... existing code ... 