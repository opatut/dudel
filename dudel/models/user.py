from dudel import app, db, gravatar
from flask import abort
from uuid import uuid4
from datetime import datetime, timedelta
import scrypt, random, pytz
from .member import Member
from .invitation import Invitation
from .group import Group
from .vote import Vote
from .accesstoken import AccessToken

class User(Member):
    id = db.Column(db.Integer, db.ForeignKey("member.id"), primary_key=True)

    login = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)

    display_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)

    preferred_language = db.Column(db.String(80), nullable=True)
    autowatch = db.Column(db.Boolean, default=False, nullable=False)
    allow_invitation_mails = db.Column(db.Boolean, default=True, nullable=False)

    # relationships
    watches = db.relationship("PollWatch", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    groups_admin = db.relationship("Group", backref="admin", lazy="dynamic", foreign_keys=[Group.admin_id])
    comments = db.relationship("Comment", backref="user", lazy="dynamic")
    invitations = db.relationship("Invitation", backref="user", lazy="dynamic", foreign_keys=[Invitation.user_id])
    invitations_created = db.relationship("Invitation", backref="creator", lazy="dynamic", foreign_keys=[Invitation.creator_id])
    votes = db.relationship("Vote", backref="user", lazy="dynamic", foreign_keys=[Vote.user_id])
    votes_assigned = db.relationship("Vote", backref="assigned_by", lazy="dynamic", foreign_keys=[Vote.assigned_by_id])
    access_tokens = db.relationship("AccessToken", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }

    def set_password(self, password):
        salt = ''.join(chr(random.randint(0,255)) for i in range(256))
        hashed_password = scrypt.encrypt(salt, password.encode('utf-8'), maxtime=0.5)
        self.password = bytearray(hashed_password)

    def check_password(self, password, maxtime=300):
        try:
            scrypt.decrypt(self.password, password.encode('utf-8'), maxtime)
            return True
        except scrypt.error as e:
            return False

    def get_avatar(self, size):
        return gravatar(self.email, size)

    @property
    def attributes(self):
        lst = [
            ('login', True),
            ('user', self.id),
            ('scope', '*'),
        ]

        if self.login in app.config.get('ADMINS', []):
            lst.append(('admin'))

        lst += [('poll_owner', poll.id) for poll in self.polls]

        return lst


    def generate_access_token(self, application=None, scope=None, ttl=3600):
        return AccessToken(
                id=str(uuid4()),
                application_id=application.id if hasattr(application, 'id') else application,
                user_id=self.id,
                scope=scope,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl),
        )
