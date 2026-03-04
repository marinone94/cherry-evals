"""add curation_events table

Revision ID: 003_add_curation_events
Revises: 47e8ef9880f4
Create Date: 2026-03-04 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_curation_events"
down_revision: str | Sequence[str] | None = "47e8ef9880f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "curation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column("example_id", sa.Integer(), nullable=True),
        sa.Column("collection_id", sa.Integer(), nullable=True),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("search_mode", sa.String(length=50), nullable=True),
        sa.Column("result_position", sa.Integer(), nullable=True),
        sa.Column("result_score", sa.Float(), nullable=True),
        sa.Column("export_format", sa.String(length=50), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["example_id"], ["examples.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_curation_events_id"), "curation_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_curation_events_event_type"), "curation_events", ["event_type"], unique=False
    )
    op.create_index(
        op.f("ix_curation_events_session_id"), "curation_events", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_curation_events_user_id"), "curation_events", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_curation_events_created_at"), "curation_events", ["created_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_curation_events_created_at"), table_name="curation_events")
    op.drop_index(op.f("ix_curation_events_user_id"), table_name="curation_events")
    op.drop_index(op.f("ix_curation_events_session_id"), table_name="curation_events")
    op.drop_index(op.f("ix_curation_events_event_type"), table_name="curation_events")
    op.drop_index(op.f("ix_curation_events_id"), table_name="curation_events")
    op.drop_table("curation_events")
