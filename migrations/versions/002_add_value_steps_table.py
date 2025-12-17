"""Add value_steps table with sort order

Revision ID: 002_value_steps
Revises: 1748b802796a
Create Date: 2025-12-17

Changes:
- Create value_steps table with sort_order for manufacturing chain sequence
- Add value_step_id FK to challenges table
- Migrate existing value_step string data to new FK relationship
- Remove old value_step string column from challenges
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_value_steps'
down_revision = '1748b802796a'
branch_labels = None
depends_on = None

# Default value steps in manufacturing order
DEFAULT_VALUE_STEPS = [
    (1, 'Upstream', 1, 'Initial manufacturing steps including cell culture, fermentation, synthesis'),
    (2, 'Downstream', 2, 'Purification, crystallization, and processing steps'),
    (3, 'Conjugation', 3, 'Conjugation and linking steps for complex molecules'),
    (4, 'Fill & Finish', 4, 'Final formulation, filling, and finishing operations'),
    (5, 'Assembly', 5, 'Device assembly and packaging'),
    (6, 'QC/Reg', 6, 'Quality control and regulatory compliance steps'),
]


def upgrade():
    # 1. Create value_steps table
    op.create_table('value_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('sort_order')
    )

    # 2. Insert default value steps
    value_steps_table = sa.table('value_steps',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('sort_order', sa.Integer),
        sa.column('description', sa.Text)
    )

    op.bulk_insert(value_steps_table, [
        {'id': id, 'name': name, 'sort_order': order, 'description': desc}
        for id, name, order, desc in DEFAULT_VALUE_STEPS
    ])

    # 3. Add value_step_id column to challenges (nullable initially)
    op.add_column('challenges',
        sa.Column('value_step_id', sa.Integer(), nullable=True)
    )

    # 4. Migrate existing data: map value_step strings to value_step_id
    # Using raw SQL for data migration
    connection = op.get_bind()

    # Get all value steps for mapping
    for id, name, order, desc in DEFAULT_VALUE_STEPS:
        connection.execute(
            sa.text("""
                UPDATE challenges
                SET value_step_id = :step_id
                WHERE value_step = :step_name
            """),
            {'step_id': id, 'step_name': name}
        )

    # 5. Add foreign key constraint
    op.create_foreign_key(
        'fk_challenges_value_step_id',
        'challenges', 'value_steps',
        ['value_step_id'], ['id']
    )

    # 6. Drop old value_step string column
    op.drop_column('challenges', 'value_step')


def downgrade():
    # 1. Add back the value_step string column
    op.add_column('challenges',
        sa.Column('value_step', sa.String(length=100), nullable=True)
    )

    # 2. Migrate data back: value_step_id → value_step string
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE challenges c
            SET value_step = vs.name
            FROM value_steps vs
            WHERE c.value_step_id = vs.id
        """)
    )

    # 3. Drop foreign key and column
    op.drop_constraint('fk_challenges_value_step_id', 'challenges', type_='foreignkey')
    op.drop_column('challenges', 'value_step_id')

    # 4. Drop value_steps table
    op.drop_table('value_steps')
