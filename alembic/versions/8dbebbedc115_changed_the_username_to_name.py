"""changed the username to name

Revision ID: 8dbebbedc115
Revises: 297cdcb0e9d4
Create Date: 2025-03-12 01:03:16.688385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dbebbedc115'
down_revision: Union[str, None] = '297cdcb0e9d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
