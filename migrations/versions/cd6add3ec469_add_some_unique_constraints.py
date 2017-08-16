"""add some unique constraints

Revision ID: cd6add3ec469
Revises: 250e3d22d78e
Create Date: 2017-08-16 17:03:55.180080

"""

# revision identifiers, used by Alembic.
revision = 'cd6add3ec469'
down_revision = '250e3d22d78e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_unique_constraint("unique_user_name", "user",
            ["username"])
    op.create_unique_constraint("unique_user_email", "user", ["email"])

def downgrade():
    op.drop_constraint("unique_user_name")
    op.drop_constraint("unique_user_email")
