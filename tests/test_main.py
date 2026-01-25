"""Тесты основных маршрутов"""
import pytest
from app import create_app


@pytest.fixture
def client():
    """Фикстура для тестирования"""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'


def test_health_check(client):
    """Тест проверки здоровья"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
