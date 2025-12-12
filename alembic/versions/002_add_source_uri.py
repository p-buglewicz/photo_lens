"""Add source_uri column and unique constraint to photos.

Revision ID: 002_add_source_uri
Revises: 001_initial_schema
Create Date: 2025-12-12 00:00:00.000000

"""

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_source_uri"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("photos", sa.Column("source_uri", sa.String(length=512), nullable=True))
    op.create_unique_constraint("uq_photos_source_uri", "photos", ["source_uri"])


def downgrade() -> None:
    op.drop_constraint("uq_photos_source_uri", "photos", type_="unique")
    op.drop_column("photos", "source_uri")
