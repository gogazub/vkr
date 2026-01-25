"""Основные маршруты"""
from flask import jsonify
from . import main_bp


@main_bp.route('/', methods=['GET'])
def index():
    """Главная страница"""
    return jsonify({
        'message': 'Добро пожаловать в микросервис',
        'status': 'ok'
    })


@main_bp.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'service': 'microservice'
    }), 200
