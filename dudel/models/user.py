from dudel import app, db, gravatar
from flask import abort
import scrypt
import random
from .member import Member
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
    username = db.Column(db.String(80))
    password = db.Column(db.LargeBinary)
    _displayname = db.Column(db.String(80))
    email = db.Column(db.String(80))
    preferred_language = db.Column(db.String(80))
    autowatch = db.Column(db.Boolean, default=False)

    # relationships
    watches = db.relationship("PollWatch", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    comments = db.relationship("Comment", backref="user", lazy="dynamic")
    votes = db.relationship("Vote", backref="user", lazy="dynamic")

    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }

    @property
    def displayname(self):
        return self._displayname or ((app.config["NAME_FORMAT"] if "NAME_FORMAT" in app.config else "%(firstname)s (%(username)s)") % {
            "firstname": self.firstname,
            "lastname": self.lastname,
            "username": self.username,
            "email": self.email
            })

    # login stuff
    def get_id(self):
        return self.username

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    @property
    def is_admin(self):
        return "ADMINS" in app.config and self.username in app.config["ADMINS"]

    def require_admin(self):
        if not self.is_authenticated() or not self.is_admin:
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

    @property
    def poll_list(self):
        from dudel.models.poll import Poll
        from dudel.models.group import Group, group_users
        # TODO: try to do it in SQL
        watched = [watch.poll for watch in self.watches if not watch.poll.deleted]
        owned = self.polls.filter_by(deleted=False).all()
        # Owned by groups I am member of
        owned += Poll.query.filter_by(deleted=False).join(Group).join(group_users).filter_by(user_id=self.id).all()
        voted = [vote.poll for vote in self.votes if not vote.poll.deleted]
        all = watched + owned + voted
        all = list(set(all))
        all.sort(key=lambda x: x.created, reverse=True)
        return all

    def __repr__(self):
        return "<User:%s>" % self.displayname