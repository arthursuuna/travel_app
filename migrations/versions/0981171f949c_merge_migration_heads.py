"""Merge migration heads

Revision ID: 0981171f949c
Revises: add_total_revenue_to_tour, bb60f138357e
Create Date: 2025-07-13 17:01:02.609549

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0981171f949c'
down_revision = ('add_total_revenue_to_tour', 'bb60f138357e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
