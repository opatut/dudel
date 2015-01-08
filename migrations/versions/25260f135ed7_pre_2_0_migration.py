"""pre-2.0 migration

Revision ID: 25260f135ed7
Revises: 2fe4543050a8
Create Date: 2015-01-08 09:14:16.998528

"""

# revision identifiers, used by Alembic.
revision = '25260f135ed7'
down_revision = '2fe4543050a8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('member',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=True),
        sa.Column('type', sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('group',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=True),
        sa.Column('identifier', sa.String(length=80), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('group_users',
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['group.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('invitation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('poll_id', sa.Integer(), nullable=True),
        sa.Column('vote_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['poll_id'], ['poll.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['vote_id'], ['vote.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'poll', sa.Column('require_invitation', sa.Boolean(), nullable=True))
    op.add_column(u'poll', sa.Column('show_invitations', sa.Boolean(), nullable=True))
    op.add_column(u'user', sa.Column('allow_invitation_mails', sa.Boolean(), nullable=True))
    op.add_column(u'user', sa.Column('autowatch', sa.Boolean(), nullable=True))
    op.add_column(u'user', sa.Column('password', sa.LargeBinary(), nullable=True))
    op.add_column(u'vote', sa.Column('assigned_by_id', sa.Integer(), nullable=True))

    # Create members from existing user objects
    op.execute("INSERT INTO member (id, source, type) (SELECT id, 'ldap', 'user' FROM \"user\");")

    # Rename author_id to owner_id, update the foreign key constraint
    op.alter_column(u'poll', u'author_id', new_column_name=u'owner_id')
    op.drop_constraint("poll_author_id_fkey", "poll")
    op.create_foreign_key("poll_owner_id_fkey", "poll", "user", ["owner_id"], ["id"])

def downgrade():
    op.drop_column(u'vote', 'assigned_by_id')
    op.drop_column(u'user', 'password')
    op.drop_column(u'user', 'autowatch')
    op.drop_column(u'user', 'allow_invitation_mails')
    op.alter_column(u'poll', u'owner_id', new_column_name=u'author_id')
    op.drop_constraint("poll_owner_id_fkey", "poll")
    op.create_foreign_key("poll_author_id_fkey", "poll", "user", ["author_id"], ["id"])
    op.drop_column(u'poll', 'show_invitations')
    op.drop_column(u'poll', 'require_invitation')
    op.drop_table('invitation')
    op.drop_table('group_users')
    op.drop_table('group')
    op.drop_table('member')
