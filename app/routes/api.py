"""API маршруты"""
from flask import request, jsonify
from . import api_bp
from app.services.example_service import ExampleService


service = ExampleService()


@api_bp.route('/items', methods=['GET'])
def get_items():
    """Получить все элементы"""
    items = service.get_all_items()
    return jsonify(items), 200


@api_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Получить элемент по ID"""
    item = service.get_item(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify(item), 200


@api_bp.route('/items', methods=['POST'])
def create_item():
    """Создать новый элемент"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    item = service.create_item(data)
    return jsonify(item), 201
