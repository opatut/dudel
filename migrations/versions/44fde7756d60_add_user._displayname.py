"""Add user._displayname column.

Revision ID: 44fde7756d60
Revises: 43e69c019c41
Create Date: 2014-06-14 04:45:29.423727

"""

revision = '44fde7756d60'
down_revision = '43e69c019c41'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('user', sa.Column('_displayname', sa.String(length=80), default="", nullable=False))

def downgrade():
    op.drop_column('user', '_displayname')
