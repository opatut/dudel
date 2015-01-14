"""Add group admin

Revision ID: 250e3d22d78e
Revises: 32f914b0065f
Create Date: 2015-01-14 21:30:23.524882

"""

# revision identifiers, used by Alembic.
revision = '250e3d22d78e'
down_revision = '32f914b0065f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column('admin_id', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('group', 'admin_id')
