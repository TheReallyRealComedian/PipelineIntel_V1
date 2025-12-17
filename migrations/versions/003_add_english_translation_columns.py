"""Add English translation columns for i18n support

Revision ID: 003_i18n_english
Revises: 002_value_steps
Create Date: 2025-12-17

Changes:
- Add _en suffix columns for all translatable text fields
- Existing fields remain as German (default)
- New _en fields are nullable, to be filled manually
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_i18n_english'
down_revision = '002_value_steps'
branch_labels = None
depends_on = None


def upgrade():
    # === ValueStep ===
    op.add_column('value_steps',
        sa.Column('name_en', sa.String(length=100), nullable=True))
    op.add_column('value_steps',
        sa.Column('description_en', sa.Text(), nullable=True))

    # === Challenge ===
    op.add_column('challenges',
        sa.Column('name_en', sa.String(length=255), nullable=True))
    op.add_column('challenges',
        sa.Column('agnostic_description_en', sa.Text(), nullable=True))
    op.add_column('challenges',
        sa.Column('agnostic_root_cause_en', sa.Text(), nullable=True))

    # === ChallengeModalityDetail ===
    op.add_column('challenge_modality_details',
        sa.Column('specific_description_en', sa.Text(), nullable=True))
    op.add_column('challenge_modality_details',
        sa.Column('specific_root_cause_en', sa.Text(), nullable=True))
    op.add_column('challenge_modality_details',
        sa.Column('impact_details_en', sa.Text(), nullable=True))
    op.add_column('challenge_modality_details',
        sa.Column('maturity_details_en', sa.Text(), nullable=True))
    op.add_column('challenge_modality_details',
        sa.Column('trends_3_5_years_en', sa.Text(), nullable=True))

    # === Modality ===
    op.add_column('modalities',
        sa.Column('modality_name_en', sa.String(length=255), nullable=True))
    op.add_column('modalities',
        sa.Column('label_en', sa.String(length=255), nullable=True))
    op.add_column('modalities',
        sa.Column('short_description_en', sa.Text(), nullable=True))
    op.add_column('modalities',
        sa.Column('description_en', sa.Text(), nullable=True))


def downgrade():
    # === Modality ===
    op.drop_column('modalities', 'description_en')
    op.drop_column('modalities', 'short_description_en')
    op.drop_column('modalities', 'label_en')
    op.drop_column('modalities', 'modality_name_en')

    # === ChallengeModalityDetail ===
    op.drop_column('challenge_modality_details', 'trends_3_5_years_en')
    op.drop_column('challenge_modality_details', 'maturity_details_en')
    op.drop_column('challenge_modality_details', 'impact_details_en')
    op.drop_column('challenge_modality_details', 'specific_root_cause_en')
    op.drop_column('challenge_modality_details', 'specific_description_en')

    # === Challenge ===
    op.drop_column('challenges', 'agnostic_root_cause_en')
    op.drop_column('challenges', 'agnostic_description_en')
    op.drop_column('challenges', 'name_en')

    # === ValueStep ===
    op.drop_column('value_steps', 'description_en')
    op.drop_column('value_steps', 'name_en')
