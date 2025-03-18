"""updated the accounts models

Revision ID: bf56e0fb85c9
Revises: 8dbebbedc115
Create Date: 2025-03-13 17:23:39.759663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf56e0fb85c9'
down_revision: Union[str, None] = '8dbebbedc115'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
