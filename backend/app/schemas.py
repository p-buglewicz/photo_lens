"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str


class IngestConfigResponse(BaseModel):
    """Ingestion configuration returned to clients."""

    takeout_path: str | None
    source: str
    limit: int | None = Field(default=None, ge=0)
    reprocess: bool | None = None


class UpdateIngestConfigRequest(BaseModel):
    """Payload for updating ingestion configuration."""

    takeout_path: str | None = None
    limit: int | None = Field(default=None, ge=0)
    reprocess: bool | None = None
