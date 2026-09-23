"""add active timer unique index

Revision ID: d1c3afcbb967
Revises: 15ec87db5d1d
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d1c3afcbb967"
down_revision: Union[str, Sequence[str], None] = "15ec87db5d1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_time_entries_active_project",
        "time_entries",
        ["project_id"],
        unique=True,
        postgresql_where="ended_at IS NULL",
    )


def downgrade() -> None:
    op.drop_index(
        "uq_time_entries_active_project",
        table_name="time_entries",
    )