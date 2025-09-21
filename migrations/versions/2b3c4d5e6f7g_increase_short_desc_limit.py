"""Increase short_description limit by changing type to Text

Revision ID: 2b3c4d5e6f7g
Revises: 1a2b3c4d5e6f
Create Date: 2025-07-17 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b3c4d5e6f7g'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade():
    # Change the column type from VARCHAR(255) to TEXT for all short_description fields
    op.alter_column('manufacturing_challenges', 'short_description',
               existing_type=sa.String(length=255),
               type_=sa.Text(),
               existing_nullable=True)
    op.alter_column('manufacturing_technologies', 'short_description',
               existing_type=sa.String(length=255),
               type_=sa.Text(),
               existing_nullable=True)
    op.alter_column('modalities', 'short_description',
               existing_type=sa.String(length=255),
               type_=sa.Text(),
               existing_nullable=True)
    op.alter_column('process_stages', 'short_description',
               existing_type=sa.String(length=255),
               type_=sa.Text(),
               existing_nullable=True)
    op.alter_column('products', 'short_description',
               existing_type=sa.String(length=255),
               type_=sa.Text(),
               existing_nullable=True)


def downgrade():
    # Revert the column type from TEXT back to VARCHAR(255)
    op.alter_column('products', 'short_description',
               existing_type=sa.Text(),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.alter_column('process_stages', 'short_description',
               existing_type=sa.Text(),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.alter_column('modalities', 'short_description',
               existing_type=sa.Text(),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.alter_column('manufacturing_technologies', 'short_description',
               existing_type=sa.Text(),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.alter_column('manufacturing_challenges', 'short_description',
               existing_type=sa.Text(),
               type_=sa.String(length=255),
               existing_nullable=True)