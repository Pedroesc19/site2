"""Add discount_pct to Affiliate

Revision ID: 2de774ede7cb
Revises: ac6d50ca51ad
Create Date: 2025-07-14 19:11:04.319977

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2de774ede7cb'
down_revision = 'ac6d50ca51ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('affiliates', sa.Column('discount_pct', sa.Numeric(precision=5, scale=2), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('affiliates', 'discount_pct')
    # ### end Alembic commands ###
