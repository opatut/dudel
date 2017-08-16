from dudel import app, db, gravatar, default_timezone
from flask import abort
import scrypt
import random
import pytz
from .member import Member
from .invitation import Invitation
from .group import Group
from .vote import Vote
from dudel.login import login_provider


# password stuff (scrypt yay)
def randstr(length):
    return ''.join(chr(random.randint(0,255)) for i in range(length))


def hash_password(password, maxtime=0.5, datalength=256):
    salt = randstr(datalength)
    hashed_password = scrypt.encrypt(salt, password.encode('utf-8'), maxtime=maxtime)
    return bytearray(hashed_password)


def verify_password(hashed_password, guessed_password, maxtime=300):
    try:
        scrypt.decrypt(hashed_password, guessed_password.encode('utf-8'), maxtime)
        return True
    except scrypt.error as e:
        print "scrypt error: %s" % e    # Not fatal but a necessary measure if server is under heavy load
        return False


@login_provider("password")
def try_login_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.password and verify_password(user.password, password):
        return user
    return None


class User(Member):
    id = db.Column(db.Integer, db.ForeignKey("member.id"), primary_key=True)
    firstname = db.Column(db.String(80))
    lastname = db.Column(db.String(80))
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.LargeBinary)
    _displayname = db.Column(db.String(80))
    email = db.Column(db.String(80), unique=True)
    preferred_language = db.Column(db.String(80))
    autowatch = db.Column(db.Boolean, default=False)
    allow_invitation_mails = db.Column(db.Boolean, default=True)
    timezone_name = db.Column(db.String(40))

    # relationships
    watches = db.relationship("PollWatch", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    groups_admin = db.relationship("Group", backref="admin", lazy="dynamic", foreign_keys=[Group.admin_id])
    comments = db.relationship("Comment", backref="user", lazy="dynamic")
    invitations = db.relationship("Invitation", backref="user", lazy="dynamic", foreign_keys=[Invitation.user_id])
    invitations_created = db.relationship("Invitation", backref="creator", lazy="dynamic", foreign_keys=[Invitation.creator_id])
    votes = db.relationship("Vote", backref="user", lazy="dynamic", foreign_keys=[Vote.user_id])
    votes_assigned = db.relationship("Vote", backref="assigned_by", lazy="dynamic", foreign_keys=[Vote.assigned_by_id])

    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }

    def create(self, username=None, firstname=None, lastname=None, email=None, password=None):
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.set_password(password)

    @property
    def displayname(self):
        return self._displayname or ((app.config["NAME_FORMAT"] if "NAME_FORMAT" in app.config else "%(firstname)s (%(username)s)") % {
            "firstname": self.firstname,
            "lastname": self.lastname,
            "username": self.username,
            "email": self.email
            })

    @property
    def timezone(self):
        return pytz.timezone(self.timezone_name) if self.timezone_name else default_timezone

    # login stuff
    def get_id(self):
        return self.username

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    @property
    def is_admin(self):
        return "ADMINS" in app.config and self.username in app.config["ADMINS"]

    def require_admin(self):
        if not self.is_authenticated or not self.is_admin:
            abort(403)

    def set_password(self, password):
        self.password = hash_password(password.encode("ascii"))

    def get_avatar(self, size):
        return gravatar(self.email, size)

    def is_member(self, of):
        if not of: return False
        if of.type == "user":
            return of == self
        else:
            return self in of.users

    def get_poll_list(self, limit=None):
        from dudel.models.poll import Poll
        from dudel.models.group import Group, group_users

        # Polls I watched
        watched = [watch.poll for watch in self.watches]

        # Owned by myself
        owned = self.polls.filter_by(deleted=False).all()
        # Owned by groups I am member of
        owned += Poll.query.filter_by(deleted=False).join(Group).join(group_users).filter_by(user_id=self.id).all()

        # Polls I voted on
        voted = [vote.poll for vote in self.votes]

        # Polls I am invited to
        invited = [invite.poll for invite in self.invitations]

        # All of them, filtered, without duplicates, sorted
        my_polls = watched + owned + voted + invited
        my_polls = [poll for poll in my_polls if not poll.deleted]
        my_polls = list(set(my_polls))
        my_polls.sort(key=lambda x: x.created, reverse=True)

        if limit:
            my_polls = my_polls[:limit]

        return my_polls

    def __repr__(self):
        return "<User:%s>" % self.displayname

    def is_invited(self, poll):
        return self.invitations.filter_by(poll_id=poll.id).count() > 0

    def get_open_invitations(self):
        return self.invitations.filter_by(vote=None)
