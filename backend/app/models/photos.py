"""SQLAlchemy ORM models for LensAnalytics."""

from sqlalchemy import BigInteger, Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from backend.app.models.base import Base


class IngestStatus(Base):
    """Track ingestion batch status."""

    __tablename__ = "ingest_status"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_files = Column(Integer, nullable=True)
    processed_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<IngestStatus batch_id={self.batch_id} status={self.status}>"


class Photo(Base):
    """Store photo metadata and embeddings."""

    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    google_id = Column(String(255), nullable=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    taken_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    exif_metadata = Column(JSONB, nullable=True)
    embedding = Column(JSONB, nullable=True)  # Store embedding as JSONB array
    batch_id = Column(String(255), ForeignKey("ingest_status.batch_id"), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_photos_taken_at", "taken_at"),
        Index("idx_photos_filename", "filename"),
        Index("idx_photos_batch_id", "batch_id"),
        Index("idx_photos_embedding", "embedding", postgresql_using="ivfflat"),
    )

    def __repr__(self) -> str:
        return f"<Photo filename={self.filename} taken_at={self.taken_at}>"
