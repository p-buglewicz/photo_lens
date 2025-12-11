# Core module exports
# Avoid importing database objects here to prevent eager engine creation
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

__all__ = [
    "settings",
    "get_logger",
]
