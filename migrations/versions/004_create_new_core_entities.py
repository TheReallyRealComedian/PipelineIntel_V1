"""Create new core entities: DrugSubstance, DrugProduct, Project

Revision ID: 004_core_entities
Revises: 003_i18n_english
Create Date: 2026-02-05

Changes:
- Create drug_substances table
- Create drug_products table
- Create projects table
- Create junction tables:
  - project_drug_substances
  - project_drug_products
  - drug_substance_drug_products
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_core_entities'
down_revision = '003_i18n_english'
branch_labels = None
depends_on = None


def upgrade():
    # === 1. Drug Substances Table ===
    op.create_table('drug_substances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('inn', sa.String(length=255), nullable=True),

        # Technical Information
        sa.Column('molecule_type', sa.String(length=100), nullable=True),
        sa.Column('mechanism_of_action', sa.Text(), nullable=True),
        sa.Column('technology', sa.Text(), nullable=True),
        sa.Column('storage_conditions', sa.String(length=255), nullable=True),
        sa.Column('shelf_life', sa.String(length=100), nullable=True),

        # Site Information
        sa.Column('development_approach', sa.String(length=100), nullable=True),
        sa.Column('development_site', sa.String(length=255), nullable=True),
        sa.Column('launch_site', sa.String(length=255), nullable=True),
        sa.Column('release_site', sa.String(length=255), nullable=True),
        sa.Column('routine_site', sa.String(length=255), nullable=True),

        # Volume Information
        sa.Column('demand_category', sa.String(length=50), nullable=True),
        sa.Column('demand_launch_year', sa.String(length=50), nullable=True),
        sa.Column('demand_peak_year', sa.String(length=50), nullable=True),
        sa.Column('peak_demand_range', sa.String(length=100), nullable=True),

        # Meta
        sa.Column('commercial', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('biel', sa.String(length=10), nullable=True),
        sa.Column('d_and_dl_ops', sa.Text(), nullable=True),
        sa.Column('last_refresh', sa.Date(), nullable=True),

        # FK to Modality (optional)
        sa.Column('modality_id', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['modality_id'], ['modalities.modality_id']),
        sa.UniqueConstraint('code', name='uq_drug_substances_code')
    )
    op.create_index('ix_drug_substances_code', 'drug_substances', ['code'])
    op.create_index('ix_drug_substances_inn', 'drug_substances', ['inn'])

    # === 2. Drug Products Table ===
    op.create_table('drug_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),

        # Technical Information
        sa.Column('pharm_form', sa.String(length=100), nullable=True),
        sa.Column('technology', sa.Text(), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('storage_conditions', sa.String(length=255), nullable=True),
        sa.Column('transport_conditions', sa.String(length=255), nullable=True),
        sa.Column('holding_time', sa.String(length=100), nullable=True),

        # Site Information
        sa.Column('development_approach', sa.String(length=100), nullable=True),
        sa.Column('development_site', sa.String(length=255), nullable=True),
        sa.Column('launch_site', sa.String(length=255), nullable=True),
        sa.Column('release_site', sa.String(length=255), nullable=True),
        sa.Column('routine_site', sa.String(length=255), nullable=True),

        # Volume Information
        sa.Column('demand_category', sa.String(length=50), nullable=True),
        sa.Column('demand_launch_year', sa.String(length=50), nullable=True),
        sa.Column('demand_peak_year', sa.String(length=50), nullable=True),
        sa.Column('peak_demand_range', sa.String(length=100), nullable=True),

        # Meta
        sa.Column('commercial', sa.String(length=50), nullable=True),
        sa.Column('strategic_technology', sa.Text(), nullable=True),
        sa.Column('d_and_dl_ops', sa.Text(), nullable=True),
        sa.Column('last_refresh', sa.Date(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_drug_products_code')
    )
    op.create_index('ix_drug_products_code', 'drug_products', ['code'])

    # === 3. Projects Table ===
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),

        # Project Information
        sa.Column('indication', sa.String(length=255), nullable=True),
        sa.Column('project_type', sa.String(length=50), nullable=True),
        sa.Column('administration', sa.String(length=100), nullable=True),

        # Timeline Milestones
        sa.Column('sod', sa.Date(), nullable=True),      # Start of Development
        sa.Column('dsmm3', sa.Date(), nullable=True),    # DS Manufacturing Milestone 3
        sa.Column('dsmm4', sa.Date(), nullable=True),    # DS Manufacturing Milestone 4
        sa.Column('dpmm3', sa.Date(), nullable=True),    # DP Manufacturing Milestone 3
        sa.Column('dpmm4', sa.Date(), nullable=True),    # DP Manufacturing Milestone 4
        sa.Column('rofd', sa.Date(), nullable=True),     # Ready for Filing Decision
        sa.Column('submission', sa.Date(), nullable=True),  # Regulatory Submission
        sa.Column('launch', sa.Date(), nullable=True),   # Market Launch

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_projects_name')
    )
    op.create_index('ix_projects_name', 'projects', ['name'])
    op.create_index('ix_projects_indication', 'projects', ['indication'])
    op.create_index('ix_projects_launch', 'projects', ['launch'])

    # === 4. Junction Table: Project <-> Drug Substance ===
    op.create_table('project_drug_substances',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('drug_substance_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('project_id', 'drug_substance_id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['drug_substance_id'], ['drug_substances.id'], ondelete='CASCADE')
    )

    # === 5. Junction Table: Project <-> Drug Product ===
    op.create_table('project_drug_products',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('drug_product_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('project_id', 'drug_product_id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['drug_product_id'], ['drug_products.id'], ondelete='CASCADE')
    )

    # === 6. Junction Table: Drug Substance <-> Drug Product (Direct Link) ===
    op.create_table('drug_substance_drug_products',
        sa.Column('drug_substance_id', sa.Integer(), nullable=False),
        sa.Column('drug_product_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('drug_substance_id', 'drug_product_id'),
        sa.ForeignKeyConstraint(['drug_substance_id'], ['drug_substances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['drug_product_id'], ['drug_products.id'], ondelete='CASCADE')
    )


def downgrade():
    # Drop junction tables first (due to FK constraints)
    op.drop_table('drug_substance_drug_products')
    op.drop_table('project_drug_products')
    op.drop_table('project_drug_substances')

    # Drop indexes
    op.drop_index('ix_projects_launch', 'projects')
    op.drop_index('ix_projects_indication', 'projects')
    op.drop_index('ix_projects_name', 'projects')
    op.drop_index('ix_drug_products_code', 'drug_products')
    op.drop_index('ix_drug_substances_inn', 'drug_substances')
    op.drop_index('ix_drug_substances_code', 'drug_substances')

    # Drop main tables
    op.drop_table('projects')
    op.drop_table('drug_products')
    op.drop_table('drug_substances')
