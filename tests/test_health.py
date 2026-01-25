"""Tests for health check endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data


def test_info_endpoint(client: TestClient):
    """Test info endpoint"""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert "debug" in data
