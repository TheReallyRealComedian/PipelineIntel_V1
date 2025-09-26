"""link_challenges_to_technologies

Revision ID: 3c90f9470525
Revises: 9c9e606941d2
Create Date: 2025-09-26 08:20:24.856304

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3c90f9470525'
down_revision = '9c9e606941d2'
branch_labels = None
depends_on = None

def upgrade():
    # Add technology_id to manufacturing_challenges
    op.add_column('manufacturing_challenges', 
                  sa.Column('technology_id', sa.Integer(), nullable=True))

    # Create foreign key constraint to manufacturing_technologies
    op.create_foreign_key('fk_challenges_technology_id',
                         'manufacturing_challenges',
                         'manufacturing_technologies',
                         ['technology_id'],
                         ['technology_id'])

    # Make the old primary_stage_id nullable as it will be deprecated
    op.alter_column('manufacturing_challenges', 'primary_stage_id',
                    existing_type=sa.Integer(),
                    nullable=True)

def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_challenges_technology_id',
                      'manufacturing_challenges',
                      type_='foreignkey')

    # Drop column
    op.drop_column('manufacturing_challenges', 'technology_id')
    
    # Note: We don't restore primary_stage_id to non-nullable in downgrade
    # to avoid potential data issues