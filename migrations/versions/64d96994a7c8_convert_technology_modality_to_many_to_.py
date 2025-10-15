"""convert_technology_modality_to_many_to_many

Revision ID: 64d96994a7c8
Revises: f2ddc3525b42
Create Date: 2025-10-15 14:01:33.404069

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '64d96994a7c8'
down_revision = 'f2ddc3525b42'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Create junction table
    op.create_table(
        'technology_modalities',
        sa.Column('technology_id', sa.Integer(), nullable=False),
        sa.Column('modality_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['technology_id'], 
                                ['manufacturing_technologies.technology_id'], 
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modality_id'], 
                                ['modalities.modality_id'], 
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('technology_id', 'modality_id')
    )
    
    op.create_index('idx_technology_modalities_tech', 
                    'technology_modalities', ['technology_id'])
    op.create_index('idx_technology_modalities_mod', 
                    'technology_modalities', ['modality_id'])
    
    # Step 2: Migrate existing data (if any) from modality_id to junction table
    op.execute("""
        INSERT INTO technology_modalities (technology_id, modality_id)
        SELECT technology_id, modality_id
        FROM manufacturing_technologies
        WHERE modality_id IS NOT NULL
    """)
    
    # Step 3: Drop the old modality_id column
    op.drop_constraint('manufacturing_technologies_modality_id_fkey', 
                       'manufacturing_technologies', type_='foreignkey')
    op.drop_index('ix_manufacturing_technologies_modality_id', 
                  table_name='manufacturing_technologies')
    op.drop_column('manufacturing_technologies', 'modality_id')
    
    print("\n" + "="*70)
    print("MANY-TO-MANY TECHNOLOGY-MODALITY MIGRATION COMPLETED")
    print("="*70)
    print("\nTechnologies can now be associated with multiple modalities.")
    print("\nTo verify:")
    print("  SELECT COUNT(*) FROM technology_modalities;")
    print("="*70 + "\n")


def downgrade():
    # Add back the single modality_id column
    op.add_column('manufacturing_technologies',
                  sa.Column('modality_id', sa.Integer(), nullable=True))
    op.create_index('ix_manufacturing_technologies_modality_id',
                    'manufacturing_technologies', ['modality_id'])
    op.create_foreign_key('manufacturing_technologies_modality_id_fkey',
                          'manufacturing_technologies', 'modalities',
                          ['modality_id'], ['modality_id'])
    
    # Migrate data back (take first modality if multiple exist)
    op.execute("""
        UPDATE manufacturing_technologies mt
        SET modality_id = (
            SELECT modality_id 
            FROM technology_modalities tm
            WHERE tm.technology_id = mt.technology_id
            LIMIT 1
        )
    """)
    
    # Drop junction table
    op.drop_index('idx_technology_modalities_mod', table_name='technology_modalities')
    op.drop_index('idx_technology_modalities_tech', table_name='technology_modalities')
    op.drop_table('technology_modalities')
    
    print("\n" + "="*70)
    print("ROLLBACK COMPLETED")
    print("technology_modalities table removed, modality_id column restored")
    print("="*70 + "\n")