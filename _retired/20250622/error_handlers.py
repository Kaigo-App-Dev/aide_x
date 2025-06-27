import logging
from flask import jsonify, render_template, request, current_app
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError
from flask_wtf.csrf import CSRFError

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """アプリケーションにエラーハンドラーを登録"""
    
    @app.errorhandler(404)
    def handle_404_error(e):
        """404エラーハンドラー"""
        logger.warning(f"404 Not Found: {request.url}")
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.',
                'status_code': 404
            }), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def handle_500_error(e):
        """500エラーハンドラー"""
        logger.error(f"500 Internal Server Error: {e}", exc_info=True)
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.',
                'status_code': 500
            }), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """CSRFエラーハンドラー"""
        logger.warning(f"CSRF Error: {e.description}")
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'error': 'CSRF Error',
                'message': 'The CSRF token is missing or invalid.',
                'status_code': 400
            }), 400
        return render_template('errors/csrf.html'), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """予期せぬエラーハンドラー"""
        if isinstance(error, HTTPException):
            return error
        
        logger.error(f"Unexpected error: {error}", exc_info=True)
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.',
                'status_code': 500
            }), 500
        return render_template('errors/500.html'), 500 