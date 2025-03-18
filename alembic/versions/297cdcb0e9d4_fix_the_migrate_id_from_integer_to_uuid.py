"""fix the Migrate id from Integer to UUID

Revision ID: 297cdcb0e9d4
Revises: 47d006045ee7
Create Date: 2025-03-10 22:32:33.291136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '297cdcb0e9d4'
down_revision: Union[str, None] = '47d006045ee7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
