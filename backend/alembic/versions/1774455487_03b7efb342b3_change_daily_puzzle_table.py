"""change daily_puzzle table

Revision ID: 03b7efb342b3
Revises: 02afffa16fe1
Create Date: 2026-03-25 12:18:07.078040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03b7efb342b3'
down_revision: Union[str, Sequence[str], None] = '02afffa16fe1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
