"""add unique constraint on users.email

Revision ID: 006_unique_user_email
Revises: 005_add_trial_ends_at
Create Date: 2026-03-10 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_unique_user_email"
down_revision: str | Sequence[str] | None = "005_add_trial_ends_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add UNIQUE constraint on users.email to prevent duplicate accounts."""
    op.create_unique_constraint("uq_users_email", "users", ["email"])


def downgrade() -> None:
    """Remove UNIQUE constraint on users.email."""
    op.drop_constraint("uq_users_email", "users", type_="unique")
