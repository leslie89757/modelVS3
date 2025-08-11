"""API 测试"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "ModelVS3 Agent Platform" in data["message"]


def test_get_agents():
    """测试获取 Agent 列表"""
    response = client.get("/api/v1/agents/")
    assert response.status_code in [200, 401]  # 可能需要认证


def test_get_models():
    """测试获取模型列表"""
    response = client.get("/api/v1/models/")
    assert response.status_code in [200, 401]  # 可能需要认证


def test_get_tools():
    """测试获取工具列表"""
    response = client.get("/api/v1/tools/")
    assert response.status_code in [200, 401]  # 可能需要认证


def test_openapi_docs():
    """测试 OpenAPI 文档"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_metrics_endpoint():
    """测试指标端点"""
    response = client.get("/metrics")
    assert response.status_code == 200 