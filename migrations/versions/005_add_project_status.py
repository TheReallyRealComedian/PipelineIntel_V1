"""Add status column to projects table

Revision ID: 005_project_status
Revises: 004_core_entities
Create Date: 2026-02-05
"""
from alembic import op
import sqlalchemy as sa

revision = '005_project_status'
down_revision = '004_core_entities'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('status', sa.String(50), nullable=True, server_default='active'))


def downgrade():
    op.drop_column('projects', 'status')
