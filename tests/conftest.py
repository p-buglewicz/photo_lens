"""Pytest configuration and fixtures."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


@pytest.fixture
def app() -> Any:
    """Create FastAPI application for testing."""
    return create_app()


@pytest.fixture
def client(app: Any) -> TestClient:
    """Create HTTP client for testing."""
    return TestClient(app)
