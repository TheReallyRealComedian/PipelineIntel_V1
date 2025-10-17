"""Add raw_conent to product

Revision ID: f521ade2ab3d
Revises: 64d96994a7c8
Create Date: 2025-10-17 16:19:45.503579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f521ade2ab3d'
down_revision = '64d96994a7c8'
branch_labels = None
depends_on = None


def upgrade():
    # Add raw_content field to products table
    op.add_column('products', sa.Column('raw_content', sa.Text(), nullable=True))


def downgrade():
    # Remove raw_content field from products table
    op.drop_column('products', 'raw_content')
