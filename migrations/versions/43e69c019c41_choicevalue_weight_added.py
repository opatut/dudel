"""ChoiceValue.weight added

Revision ID: 43e69c019c41
Revises: b35387ae159
Create Date: 2014-04-24 20:36:17.098274

"""

# revision identifiers, used by Alembic.
revision = '43e69c019c41'
down_revision = 'b35387ae159'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('choice_value', sa.Column('weight', sa.Float, server_default="0", nullable=False))
    # set default weights for existing default choice_values (yes/no/maybe)
    op.execute("""UPDATE choice_value SET weight = 0;""")
    op.execute("""UPDATE choice_value SET weight = 0.5 WHERE title = "maybe";""")
    op.execute("""UPDATE choice_value SET weight = 1 WHERE title = "yes";""")

def downgrade():
    op.drop_column('choice_value', 'weight')
