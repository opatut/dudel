from dudel import app, db
from flask import abort
from .member import Member

group_users = db.Table('group_users', db.metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('group.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class Group(Member):
    id = db.Column(db.Integer, db.ForeignKey("member.id"), primary_key=True)
    name = db.Column(db.String(80))
    identifier = db.Column(db.String(80))

    # relationships
    users = db.relationship("User", backref="groups", lazy="dynamic", secondary="group_users")

    __mapper_args__ = {
        'polymorphic_identity': 'group',
    }

    @property
    def displayname(self):
        return self.name

    # This would be required for recursive groups.
    # @property
    # def get_users(self, visited_groups=[]):
    #     users = []

    #     for member in self.members:
    #         if isinstance(member, Group):
    #             if not member in visited_groups:
    #                 visited_groups.append(member)
    #                 for user in member.get_users():
    #                     if not user in users:
    #                         users.append(user)

    #         elif isinstance(member, User):
    #             if not user in users:
    #                 users.append(user)

    #     return users
