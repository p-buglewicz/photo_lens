"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str
