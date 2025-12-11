"""Tests for configuration."""

from backend.app.core.config import settings


def test_settings_loaded() -> None:
    """Test that settings are loaded correctly."""
    assert settings is not None
    assert settings.environment in ["development", "staging", "production"]
    assert settings.debug is not None


def test_database_url_configured() -> None:
    """Test that database URL is configured."""
    assert settings.database_url is not None
    assert "postgresql" in settings.database_url


def test_default_thumbnail_cache_path() -> None:
    """Test default thumbnail cache path."""
    assert settings.thumbnail_cache is not None
    assert "/thumbnails" in settings.thumbnail_cache
