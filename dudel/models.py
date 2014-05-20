from dudel import app, db, login_manager
from flask import url_for, session, abort
from flask.ext.login import current_user
from flask.ext.babel import lazy_gettext
from datetime import datetime
import scrypt, random

class PollExpiredException(Exception):
    def __init__(self, poll):
        self.poll = poll

class PollActionException(Exception):
    def __init__(self, poll, action):
        self.poll = poll
        self.action = action

def update_user_data(username, data):
    user = User.query.filter_by(username=username).first()
    if not user:
        # create the user
        user = User()
        user.username = username
        db.session.add(user)

    if "givenName" in data:
        user.firstname = data["givenName"]
    user.lastname = data["sn"]
    user.email = data["mail"]
    db.session.commit()

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

@login_manager.user_loader
def get_user(username):
    return User.query.filter_by(username=username).first()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(80))
    lastname = db.Column(db.String(80))
    username = db.Column(db.String(80))
    password = db.Column(db.LargeBinary)
    email = db.Column(db.String(80))
    preferred_language = db.Column(db.String(80))

    @property
    def displayname(self):
        return (app.config["NAME_FORMAT"] if "NAME_FORMAT" in app.config else "%(firstname)s (%(username)s)") % {
            "firstname": self.firstname,
            "lastname": self.lastname,
            "username": self.username,
            "email": self.email
            }
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
        if not current_user.is_authenticated() or not current_user.is_admin:
            abort(403)

    def set_password(self, password):
        self.password = hash_password(password.encode("ascii"))



class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    description = db.Column(db.Text)
    slug = db.Column(db.String(80))
    type = db.Column(db.Enum("date", "normal", name="poll_type"), default="normal")
    created = db.Column(db.DateTime)
    author = db.relationship("User", backref="polls")
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # === Extra settings ===
    due_date = db.Column(db.DateTime)
    anonymous_allowed = db.Column(db.Boolean, default=True)
    public_listing = db.Column(db.Boolean, default=False)
    require_login = db.Column(db.Boolean, default=False)
    show_results = db.Column(db.Enum("summary", "complete", "never", "summary_after_vote", "complete_after_vote", name="poll_show_results"), default="complete")
    send_mail = db.Column(db.Boolean, default=False)
    one_vote_per_user = db.Column(db.Boolean, default=True)
    allow_comments = db.Column(db.Boolean, default=True)

    RESERVED_NAMES = ["login", "logout", "index", "user", "admin"]

    def __init__(self):
        self.created = datetime.utcnow()
        # create yes/no/maybe default choice values
        self.choice_values.append(ChoiceValue("yes", "check", "9C6", 1.0))
        self.choice_values.append(ChoiceValue("no", "ban", "F96", 0.0))
        self.choice_values.append(ChoiceValue("maybe", "question", "FF6", 0.5))

    @property 
    def is_expired(self):
        return self.due_date and self.due_date < datetime.utcnow()

    @property
    def show_votes(self):
        return self.show_results == "complete" or (self.show_results == "complete_after_vote" and self.is_expired)

    @property
    def show_summary(self):
        return self.show_votes or self.show_results == "summary" or (self.show_results == "summary_after_vote" and self.is_expired)

    @property
    def has_choices(self):
        return len(self.get_choices()) > 0

    def get_url(self):
        return url_for("poll", slug=self.slug)

    def get_vote_choice(self, vote, choice):
        return VoteChoice.query.filter_by(vote=vote, choice=choice).first()

    def get_choices(self):
        return Choice.query.filter_by(poll_id=self.id, deleted=False).all()

    def get_choice_values(self):
        return ChoiceValue.query.filter_by(poll_id=self.id, deleted=False).all()

    def get_choice_by_id(self, id):
        return Choice.query.filter_by(poll_id=self.id, id=id).first()

    def get_choice_dates(self):
        return list(set(choice.date.date() for choice in self.get_choices()))

    def get_choice_times(self):
        return list(set(choice.date.time() for choice in self.get_choices()))

    def has_choice_date_time(self, date, time):
        dt = datetime.combine(date, time)
        return [choice for choice in self.get_choices() if choice.date == dt and not choice.deleted]

    def user_can_edit(self, user):
        return not self.author or self.author == user or (user.is_authenticated() and user.is_admin)

    def get_user_votes(self, user):
        return [] if user.is_anonymous() else Vote.query.filter_by(poll = self, user = user).all()

    def check_expiry(self):
        if self.is_expired:
            raise PollExpiredException(self)

    def check_edit_permission(self):
        if not self.user_can_edit(current_user):
            raise PollActionException(self, lazy_gettext("edit"))

    # returns a list of groups
    # each group is sorted
    # the groups are sorted by first item
    def get_choice_groups(self):
        groups = {}
        for choice in self.get_choices():
            group = choice.group
            if not group in groups:
                groups[group] = []
            groups[group].append(choice)
        return sorted([sorted(group) for group in groups.itervalues()])

    def get_choices_by_group(self, group):
        return [choice for choice in self.get_choices() if choice.group == group]

    def get_comments(self):
        return Comment.query.filter_by(poll=self, deleted=False).order_by(db.asc(Comment.created)).all()

    def fill_vote_form(self, form):
        while form.vote_choices:
            form.vote_choices.pop_entry()

        for group in self.get_choice_groups():
            for choice in group:
                form.vote_choices.append_entry(dict(choice_id=choice.id))

        for subform in form.vote_choices:
            subform.value.choices = [(v.id, v.title) for v in self.get_choice_values()]

    def get_stats(self):
        counts = {}
        for choice in self.choices:
            counts[choice] = choice.get_counts()

        scores = {}
        totals = {}
        for choice, choice_counts in counts.items():
            totals[choice] = len(choice.vote_choices)
            scores[choice] = 0
            for value, count in choice_counts.items():
                scores[choice] += count * value.weight 

        max_score = max(scores.values())

        return scores, counts, totals, max_score

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    poll = db.relationship("Poll", backref="choices")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

    def __cmp__(self,other):
        return cmp(self.date, other.date) or cmp(self.deleted, other.deleted) or cmp(self.text, other.text)

    def get_counts(self):
        counts = {vc: 0 for vc in self.poll.choice_values}
        for vote_choice in self.vote_choices:
            if vote_choice.value:
                counts[vote_choice.value] += 1
        return counts

    @property
    def group(self):
        if self.date:
            return self.date.date()
        else:
            return "default" # normal polls only have one default group

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    created = db.Column(db.DateTime)
    name = db.Column(db.String(80))
    user = db.relationship("User", backref="comments")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    poll = db.relationship("Poll", backref="comments")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

    def user_can_edit(self, user):
        if not self.user: return True
        if user.is_anonymous(): return False
        return user == self.user or user == self.poll.author

class ChoiceValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    icon = db.Column(db.String(64))
    color = db.Column(db.String(6))
    poll = db.relationship("Poll", backref="choice_values")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Float, default=0.0)

    def __init__(self, title="", icon="question", color="EEEEEE", weight = 0.0):
        self.title = title
        self.icon = icon
        self.color = color
        self.weight = weight

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    poll = db.relationship("Poll", backref="votes")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    user = db.relationship("User", backref="votes")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    anonymous = db.Column(db.Boolean, default=False)

    def user_can_delete(self, user):
        # only if logged in
        if not user.is_authenticated(): return False
        # allow for poll author 
        if self.poll.author and self.poll.author == user: return True
        # allow for user
        if self.user: return self.user == user
        # disallow
        return False

    def user_can_edit(self, user):
        # allow for author
        if self.poll.author and self.poll.author == user: return True
        # allow for creator
        if self.user: return user == self.user
        # allow everyone, if no creator
        return True

class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    value = db.relationship("ChoiceValue", backref="vote_choices")
    value_id = db.Column(db.Integer, db.ForeignKey("choice_value.id"))
    vote = db.relationship("Vote", backref="vote_choices")
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice = db.relationship("Choice", backref="vote_choices")
    choice_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
