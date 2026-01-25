"""Маршруты приложения"""
from flask import Blueprint

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# Импортируем маршруты
from . import main, api
