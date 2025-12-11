"""Tests for health check endpoint."""

from fastapi.testclient import TestClient

from backend.app.schemas import HealthResponse


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "backend is running" in data["message"]


def test_health_check_response_model(client: TestClient) -> None:
    """Test health check response matches HealthResponse schema."""
    response = client.get("/health")
    assert response.status_code == 200
    health = HealthResponse(**response.json())
    assert health.status == "healthy"
    assert isinstance(health.message, str)
