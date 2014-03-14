"""Changed some columns to type TEXT.

Revision ID: b35387ae159
Revises: ed19f02bb1e
Create Date: 2014-03-14 17:38:16.345440

"""

# revision identifiers, used by Alembic.
revision = 'b35387ae159'
down_revision = 'ed19f02bb1e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('comment', 'text', type_=sa.Text)
    op.alter_column('vote_choice', 'comment', type_=sa.Text)

def downgrade():
    op.alter_column('comment', 'text', type_=sa.String(80))
    op.alter_column('vote_choice', 'comment', type_=sa.String(80))
