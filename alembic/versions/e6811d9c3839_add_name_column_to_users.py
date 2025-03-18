"""add name column to users

Revision ID: e6811d9c3839
Revises: bf56e0fb85c9
Create Date: 2025-03-15 00:30:54.112640

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6811d9c3839'
down_revision: Union[str, None] = 'bf56e0fb85c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
