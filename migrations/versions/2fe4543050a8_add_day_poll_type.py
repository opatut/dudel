"""Add day poll type, screw those Enum's

Revision ID: 2fe4543050a8
Revises: 54ef64095b17
Create Date: 2014-12-11 17:37:40.013013

"""

# revision identifiers, used by Alembic.
revision = '2fe4543050a8'
down_revision = '580ca7ba7446'

from alembic import op
import sqlalchemy as sa

enum_poll_type = sa.Enum("date", "normal", name="poll_type")
enum_poll_show_results = sa.Enum("summary", "complete", "never", "summary_after_vote", "complete_after_vote", name="poll_show_results")

def upgrade():
    op.alter_column('poll', 'show_results', type_=sa.String(20))
    op.alter_column('poll', 'type', type_=sa.String(20))

def downgrade():
    op.alter_column('poll', 'show_results', type_=enum_poll_type)
    op.alter_column('poll', 'type', type_=enum_poll_show_results)
