"""add_modality_challenges_table

Revision ID: c19e20288615
Revises: 2242d7e652fb
Create Date: 2025-10-05 12:17:35.671245

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c19e20288615'
down_revision = '2242d7e652fb'
branch_labels = None
depends_on = None


def upgrade():
    # Create the modality_challenges table
    op.create_table(
        'modality_challenges',
        sa.Column('modality_id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('is_typical', sa.Boolean(), server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['challenge_id'], 
                                ['manufacturing_challenges.challenge_id'], 
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modality_id'], 
                                ['modalities.modality_id'], 
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('modality_id', 'challenge_id')
    )
    
    # Create indexes
    op.create_index('idx_modality_challenges_modality', 
                    'modality_challenges', ['modality_id'])
    op.create_index('idx_modality_challenges_challenge', 
                    'modality_challenges', ['challenge_id'])
    
    # Migrate data from standard_challenges JSONB to modality_challenges table
    op.execute("""
        INSERT INTO modality_challenges (modality_id, challenge_id, is_typical)
        SELECT 
            m.modality_id,
            mc.challenge_id,
            true
        FROM modalities m
        CROSS JOIN jsonb_array_elements_text(m.standard_challenges) AS challenge_name
        INNER JOIN manufacturing_challenges mc 
            ON mc.challenge_name = challenge_name::text
        WHERE m.standard_challenges IS NOT NULL
    """)
    
    print("\n" + "="*70)
    print("MODALITY CHALLENGES MIGRATION COMPLETED")
    print("="*70)
    print("\nMigrated challenge links from JSONB to normalized table.")
    print("\nTo verify:")
    print("  SELECT COUNT(*) FROM modality_challenges;")
    print("\nNote: modalities.standard_challenges field preserved for reference.")
    print("="*70 + "\n")


def downgrade():
    op.drop_index('idx_modality_challenges_challenge', table_name='modality_challenges')
    op.drop_index('idx_modality_challenges_modality', table_name='modality_challenges')
    op.drop_table('modality_challenges')
    
    print("\n" + "="*70)
    print("ROLLBACK COMPLETED")
    print("modality_challenges table removed")
    print("="*70 + "\n")