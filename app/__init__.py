"""Микросервис приложение"""
from flask import Flask


def create_app():
    """Фабрика приложения"""
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    # Регистрация blueprint'ов
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
