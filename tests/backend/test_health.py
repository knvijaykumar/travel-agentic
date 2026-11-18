import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def test_client():
    """Test client for FastAPI endpoints."""
    return TestClient(app)


def test_root_endpoint(test_client):
    """Verify root endpoint returns project metadata."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["health"] == "/health"


def test_root_health_endpoint(test_client):
    """Verify root /health endpoint returns healthy status."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "app_name" in data


def test_api_v1_health_endpoint(test_client):
    """Verify /api/v1/health endpoint works identically."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_cors_preflight_headers(test_client):
    """Verify CORS preflight headers respond to allowed origins."""
    response = test_client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "GET" in response.headers.get("access-control-allow-methods", "")


def test_cors_simple_request_headers(test_client):
    """Verify CORS headers accompany regular GET responses."""
    response = test_client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
