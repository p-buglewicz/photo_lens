"""Initial schema setup with ingest_status and photos tables.

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-12-11 00:00:00.000000

"""

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    # Create pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create ingest_status table
    op.create_table(
        "ingest_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.String(255), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("total_files", sa.Integer(), nullable=True),
        sa.Column("processed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create photos table
    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("taken_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("embedding", postgresql.JSONB(), nullable=True),
        sa.Column("batch_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["ingest_status.batch_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_photos_taken_at", "photos", ["taken_at"])
    op.create_index("idx_photos_filename", "photos", ["filename"])
    op.create_index("idx_photos_batch_id", "photos", ["batch_id"])


def downgrade() -> None:
    """Drop initial schema."""
    op.drop_index("idx_photos_batch_id")
    op.drop_index("idx_photos_filename")
    op.drop_index("idx_photos_taken_at")
    op.drop_table("photos")
    op.drop_table("ingest_status")
    op.execute("DROP EXTENSION IF EXISTS vector")
