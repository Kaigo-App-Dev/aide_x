"""
共通デコレータモジュール
"""
from functools import wraps
from flask import current_app, redirect, url_for, flash
from flask_login import current_user

def login_required(f):
    """ログイン必須のデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('このページにアクセスするにはログインが必要です。', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理者権限必須のデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('このページにアクセスするには管理者権限が必要です。', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """特定のロールが必要なデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or role not in current_user.roles:
                flash(f'このページにアクセスするには{role}の権限が必要です。', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator 