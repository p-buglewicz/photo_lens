"""Tests for FastAPI application initialization."""

from backend.app.main import create_app


def test_create_app() -> None:
    """Test that FastAPI application is created successfully."""
    app = create_app()
    assert app is not None
    assert app.title == "LensAnalytics API"
    assert app.version == "0.1.0"


def test_app_routes() -> None:
    """Test that expected routes are registered."""
    app = create_app()
    routes = [getattr(route, "path", None) for route in app.routes]
    assert "/health" in routes


def test_app_cors_middleware() -> None:
    """Test that CORS middleware is configured."""
    app = create_app()
    middlewares = [middleware for middleware in app.user_middleware]
    assert len(middlewares) > 0
