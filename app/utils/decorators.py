"""Декораторы"""
from functools import wraps
from flask import jsonify


def handle_exceptions(f):
    """Декоратор для обработки исключений"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function
