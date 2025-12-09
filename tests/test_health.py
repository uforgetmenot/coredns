"""
测试健康检查和基础端点
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "coredns-manager"
    assert "version" in data


def test_root_redirects_to_dashboard():
    """根路径应重定向到 Dashboard"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"


def test_api_docs():
    """测试 API 文档可访问"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc():
    """测试 ReDoc 文档可访问"""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_schema():
    """测试 OpenAPI schema 可访问"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "CoreDNS Manager"
    assert schema["info"]["version"] == "1.0.0"
