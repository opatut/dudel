"""Add timezone support, fix timings

Revision ID: 32f914b0065f
Revises: 25260f135ed7
Create Date: 2015-01-13 22:20:58.774777

"""

# revision identifiers, used by Alembic.
revision = '32f914b0065f'
down_revision = '25260f135ed7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('poll', sa.Column('timezone_name', sa.String(length=40), nullable=True))
    op.add_column('user', sa.Column('timezone_name', sa.String(length=40), nullable=True))

    ## This is how you can update the datetimes: ##
    # SET timezone = 'Europe/Berlin';
    # UPDATE choice SET date = date::timestamptz AT TIME ZONE 'UTC';
    # UPDATE poll SET timezone_name = 'Europe/Berlin', due_date = due_date::timestamptz AT TIME ZONE 'UTC';

def downgrade():
    op.drop_column('user', 'timezone_name')
    op.drop_column('poll', 'timezone_name')
