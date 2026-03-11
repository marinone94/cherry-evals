"""add trial_ends_at to users

Revision ID: 005_add_trial_ends_at
Revises: 004_add_users_and_api_keys
Create Date: 2026-03-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_trial_ends_at"
down_revision: str | Sequence[str] | None = "004_add_users_and_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add trial_ends_at column to users table."""
    op.add_column("users", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove trial_ends_at column from users table."""
    op.drop_column("users", "trial_ends_at")
