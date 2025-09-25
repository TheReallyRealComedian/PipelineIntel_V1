"""Add relationship_type to product_to_challenge

Revision ID: 9c9e606941d2
Revises: d7a70d5639a4
Create Date: 2025-09-25 15:40:22.551795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c9e606941d2'
down_revision = 'd7a70d5639a4'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to the association table
    op.add_column('product_to_challenge', 
                  sa.Column('relationship_type', sa.String(length=20), nullable=False, server_default='explicit'))
    op.add_column('product_to_challenge', 
                  sa.Column('notes', sa.Text(), nullable=True))
    
    # Create index for performance
    op.create_index('idx_product_challenge_type', 'product_to_challenge', ['product_id', 'relationship_type'])


def downgrade():
    # Remove the index
    op.drop_index('idx_product_challenge_type', table_name='product_to_challenge')
    
    # Remove the columns
    op.drop_column('product_to_challenge', 'notes')
    op.drop_column('product_to_challenge', 'relationship_type')