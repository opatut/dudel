from dudel import app, db, login_manager
from flask import url_for, session
from flask.ext.login import current_user
from datetime import datetime

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
        return (app.config["NAME_FORMAT"] if "NAME_FORMAT" in app.config else "%(firstname)s (%(username)s)") % self.__dict__

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

    RESERVED_NAMES = ["login", "logout", "index"]

    def __init__(self):
        self.created = datetime.utcnow()
        # create yes/no/maybe default choice values
        self.choice_values.append(ChoiceValue("yes", "check", "9C6"))
        self.choice_values.append(ChoiceValue("no", "ban", "F96"))
        self.choice_values.append(ChoiceValue("maybe", "question", "FF6"))

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
        return not self.author or self.author == user

    def get_user_votes(self, user):
        return [] if user.is_anonymous() else Vote.query.filter_by(poll = self, user = user).all()

    def check_expiry(self):
        if self.is_expired:
            raise PollExpiredException(self)

    def check_edit_permission(self):
        if not self.user_can_edit(current_user):
            raise PollActionException(self, "edit")

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

    def get_statistics(self):
        stats = {choice: {choice_value.title: sum([1 if vc.value == choice_value else 0 for vc in choice.vote_choices]) for choice_value in self.choice_values} for choice in self.get_choices()}
        main_key = "yes"
        maximum = max([v[main_key] for k,v in stats.iteritems()]) if stats else 0
        for k in stats:
            stats[k]["max"] = (stats[k][main_key] == maximum)
        return stats

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

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    poll = db.relationship("Poll", backref="choices")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

    def __cmp__(self,other):
        return cmp(self.date, other.date) or cmp(self.deleted, other.deleted) or cmp(self.text, other.text)

    @property
    def group(self):
        if self.date:
            return self.date.date()
        else:
            return "default" # normal polls only have one default group

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
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

    def __init__(self, title="", icon="question", color="EEEEEE"):
        self.title = title
        self.icon = icon
        self.color = color

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
    value = db.relationship("ChoiceValue", backref="vote_choices")
    value_id = db.Column(db.Integer, db.ForeignKey("choice_value.id"))
    vote = db.relationship("Vote", backref="vote_choices")
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice = db.relationship("Choice", backref="vote_choices")
    choice_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
