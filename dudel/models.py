from dudel import app, db, login_manager
from flask import url_for, session
from flask.ext.login import current_user
from datetime import datetime

def update_user_data(username, data):
    user = User.query.filter_by(username=username).first()
    if not user:
        # create the user
        user = User()
        user.username = username
        db.session.add(user)

    user.firstname = data["givenName"]
    user.lastname = data["sn"]
    user.email = data["mail"]
    db.session.commit()

@login_manager.user_loader
def get_user(username):
    return User.query.filter_by(username=username).first()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(80))
    lastname = db.Column(db.String(80))
    username = db.Column(db.String(80))
    email = db.Column(db.String(80))

    @property
    def displayname(self):
        if self.firstname and self.lastname:
            return "%s %s" % (self.firstname, self.lastname)
        else:
            return self.username

    # login stuff
    def get_id(self):
        return self.username

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    slug = db.Column(db.String(80))
    type = db.Column(db.Enum("date", "normal"), default="normal")
    created = db.Column(db.DateTime)
    author = db.relationship("User", backref="polls")
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # === Extra settings ===
    due_date = db.Column(db.DateTime)
    password = db.Column(db.String)
    # "What is impossible without password?"
    # 0: nothing, 1: editing, 2: vote, 3: show
    password_level = db.Column(db.Integer, default=0)
    anonymous_allowed = db.Column(db.Boolean, default=True)
    public_listing = db.Column(db.Boolean, default=False)
    require_login = db.Column(db.Boolean, default=False)
    show_results = db.Column(db.Enum("summary", "complete", "never", "summary_after_vote", "complete_after_vote"))
    send_mail = db.Column(db.Boolean, default=False)

    RESERVED_NAMES = ["login", "logout", "index"]

    def __init__(self):
        self.created = datetime.utcnow()

    def get_url(self):
        return url_for("poll", slug=self.slug)

    def get_vote_choice(self, vote, choice):
        return VoteChoice.query.filter_by(vote=vote, choice=choice).first()

    def get_choices(self):
        return Choice.query.filter_by(poll_id=self.id, deleted=False).all()

    def get_choice_by_id(self, id):
        return Choice.query.filter_by(poll_id=self.id, id=id).first()

    def get_choice_dates(self):
        return list(set([choice.date.date() for choice in self.get_choices()]))

    def get_choice_times(self):
        return list(set([choice.date.time() for choice in self.get_choices()]))

    def has_choice_date_time(self, date, time):
        dt = datetime.combine(date, time)
        return [choice for choice in self.get_choices() if choice.date == dt and not choice.deleted]

    def user_can_edit(self, user):
        return not self.author or self.author == user

    def get_choice_groups(self):
        return self.get_choices_grouped_by_date() if self.type == "date" else {"default": self.choices}

    def get_choices_grouped_by_date(self):
        if not self.type == "date": raise Exception("You should not get_choices_grouped_by_date on a non-date poll.")
        groups = {}
        for choice in self.get_choices():
            if not choice.date.date() in groups: groups[choice.date.date()] = []
            groups[choice.date.date()].append(choice)
        for group, li in groups.iteritems():
            li.sort(reverse=True)
        return groups

    def get_statistics(self):
        stats = {choice: {value: sum([1 if vc.value==value else 0 for vc in choice.vote_choices]) for value in ("yes", "no", "maybe")} for choice in self.get_choices()}
        maximum = max([v["yes"] for k,v in stats.iteritems()]) if stats else 0
        for k in stats:
            stats[k]["max"] = (stats[k]["yes"] == maximum)
        return stats

    # @property
    # def password_session_key(self):
    #     return "poll-password-%s" % self.id

    # def has_password(self):
    #     return (self.password_session_key in session and session[self.password_session_key] == self.password) \
    #         or (self.author and self.author == current_user)

    # def set_password(self):
    #     session[self.password_session_key] = self.password

    #e.g. "require_password(2)" for voting page, returns false if the password is
    # not set, and this poll requires pw level 2 or higher
    # def require_password(self, level):
    #     if not self.has_password():
    #         return level <= self.password_level???

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    poll = db.relationship("Poll", backref="choices")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

    def __cmp__(self,other):
        return cmp(self.date, other.date) or cmp(self.deleted, other.deleted) or cmp(self.text, other.text)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    poll = db.relationship("Poll", backref="votes")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    user = db.relationship("User", backref="votes")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    anonymous = db.Column(db.Boolean, default=False)

class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(64))
    value = db.Column(db.Enum("yes", "no", "maybe"), default="no")
    vote = db.relationship("Vote", backref="vote_choices")
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice = db.relationship("Choice", backref="vote_choices")
    choide_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
