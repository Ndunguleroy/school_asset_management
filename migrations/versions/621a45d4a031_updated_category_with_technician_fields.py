import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = '621a45d4a031'
down_revision = '6b446c0dcbc2'
branch_labels = None
depends_on = None


def upgrade():
    # Safely drop maintenance_team only if it exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'maintenance_team' in existing_tables:
        op.drop_table('maintenance_team')

    # Add technician columns to categories if they dont exist
    columns = [col['name'] for col in inspector.get_columns('categories')]

    if 'technician_name' not in columns:
        op.add_column('categories',
            sa.Column('technician_name', sa.String(length=100), nullable=True))

    if 'technician_email' not in columns:
        op.add_column('categories',
            sa.Column('technician_email', sa.String(length=100), nullable=True))

    if 'technician_phone' not in columns:
        op.add_column('categories',
            sa.Column('technician_phone', sa.String(length=20), nullable=True))


def downgrade():
    op.drop_column('categories', 'technician_phone')
    op.drop_column('categories', 'technician_email')
    op.drop_column('categories', 'technician_name')
