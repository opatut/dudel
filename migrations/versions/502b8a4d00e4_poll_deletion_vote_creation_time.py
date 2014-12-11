"""Poll deletion, vote creation time

Revision ID: 502b8a4d00e4
Revises: 54ef64095b17
Create Date: 2014-12-07 12:18:12.749654

"""

# revision identifiers, used by Alembic.
revision = '502b8a4d00e4'
down_revision = '54ef64095b17'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('poll', sa.Column('deleted', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('vote', sa.Column('created', sa.DateTime(), nullable=True))

    op.execute("UPDATE poll SET deleted = FALSE;")


def downgrade():
    op.drop_column('vote', 'created')
    op.drop_column('poll', 'deleted')
