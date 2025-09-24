"""Add label field to modalities table

Revision ID: d7a70d5639a4
Revises: de1790bb1890
Create Date: 2025-09-24 12:32:55.684524

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7a70d5639a4'
down_revision = 'de1790bb1890'
branch_labels = None
depends_on = None


def upgrade():
    # ### Only add the label field to modalities table ###
    op.add_column('modalities', sa.Column('label', sa.String(length=255), nullable=True))


def downgrade():
    # ### Remove the label field from modalities table ###
    op.drop_column('modalities', 'label')