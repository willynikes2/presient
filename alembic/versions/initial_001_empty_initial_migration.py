"""Empty initial migration

Revision ID: initial_001
Revises: 
Create Date: 2025-05-28 20:00:45

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Database already has tables, this is just to establish baseline
    pass


def downgrade() -> None:
    # Nothing to downgrade
    pass
