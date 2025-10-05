"""Add process_template_id to products table

Revision ID: 2242d7e652fb
Revises: 3c90f9470525
Create Date: 2025-10-05 14:30:00.000000

This migration adds the process_template_id foreign key to the products table,
enabling explicit links from products to their manufacturing process templates.
This completes the inheritance chain: Product → Template → TemplateStages → base_capabilities
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2242d7e652fb'
down_revision = '3c90f9470525'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add process_template_id to products table with intelligent backfilling.
    """
    # Step 1: Add the new column as nullable
    op.add_column('products',
        sa.Column('process_template_id', sa.Integer(), nullable=True)
    )

    # Step 2: Add the foreign key constraint
    op.create_foreign_key(
        'fk_products_process_template_id',
        'products', 'process_templates',
        ['process_template_id'], ['template_id'],
        ondelete='SET NULL'  # If template deleted, just NULL the reference
    )

    # Step 3: Create an index for performance (products will be queried by template)
    op.create_index(
        'ix_products_process_template_id',
        'products',
        ['process_template_id']
    )

    # Step 4: Intelligent backfill for existing products
    # Only auto-assign if a modality has EXACTLY ONE template
    op.execute("""
        UPDATE products p
        SET process_template_id = (
            SELECT pt.template_id
            FROM process_templates pt
            WHERE pt.modality_id = p.modality_id
            LIMIT 1
        )
        WHERE p.modality_id IS NOT NULL
        AND (
            SELECT COUNT(*)
            FROM process_templates pt2
            WHERE pt2.modality_id = p.modality_id
        ) = 1
    """)

    # Note: We cannot use a CHECK constraint with subqueries in PostgreSQL
    # Validation will be handled at the application level via the model's @validates decorator

    print("\n" + "="*70)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nNext steps:")
    print("1. Review products with NULL process_template_id (multi-template modalities)")
    print("2. Manually assign templates to those products via the UI or SQL")
    print("3. Update your data import logic to include 'process_template_name' field")
    print("\nTo find products needing manual template assignment:")
    print("  SELECT product_code, product_name FROM products")
    print("  WHERE process_template_id IS NULL AND modality_id IS NOT NULL;")
    print("="*70 + "\n")


def downgrade():
    """
    Remove process_template_id and all related constraints.
    """
    # Drop index
    op.drop_index('ix_products_process_template_id', table_name='products')

    # Drop foreign key
    op.drop_constraint('fk_products_process_template_id', 'products', type_='foreignkey')

    # Drop column
    op.drop_column('products', 'process_template_id')

    print("\n" + "="*70)
    print("ROLLBACK COMPLETED")
    print("Products no longer have explicit template links")
    print("="*70 + "\n")