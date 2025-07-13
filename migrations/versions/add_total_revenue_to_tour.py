"""
Migration script to add total_revenue field to Tour model.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_total_revenue_to_tour"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tour",
        sa.Column("total_revenue", sa.Float(), nullable=False, server_default="0.0"),
    )


def downgrade():
    op.drop_column("tour", "total_revenue")
