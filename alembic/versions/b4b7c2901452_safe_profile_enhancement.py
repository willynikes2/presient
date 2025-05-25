"""Safe profile enhancement

Revision ID: b4b7c2901452
Revises: bb191415c329
Create Date: 2025-05-25 15:39:52.849203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4b7c2901452'
down_revision: Union[str, None] = 'bb191415c329'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
