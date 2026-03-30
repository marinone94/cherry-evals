"""add unique constraint on users.polar_customer_id

Revision ID: 007_unique_polar_customer_id
Revises: 006_unique_user_email
Create Date: 2026-03-30 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_unique_polar_customer_id"
down_revision: str | Sequence[str] | None = "006_unique_user_email"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add UNIQUE constraint on users.polar_customer_id to prevent duplicate billing records."""
    op.create_unique_constraint("uq_users_polar_customer_id", "users", ["polar_customer_id"])


def downgrade() -> None:
    """Remove UNIQUE constraint on users.polar_customer_id."""
    op.drop_constraint("uq_users_polar_customer_id", "users", type_="unique")
