from dudel import db, mail
from dudel.models.choice import Choice
from dudel.models.choicevalue import ChoiceValue
from dudel.models.comment import Comment
from dudel.models.pollwatch import PollWatch
from dudel.models.vote import Vote
from dudel.models.votechoice import VoteChoice
from dudel.util import PollExpiredException, PollActionException
from datetime import datetime, timedelta
from flask import url_for, render_template
from flask.ext.babel import lazy_gettext
from flask.ext.login import current_user
from flask.ext.mail import Message

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    description = db.Column(db.Text)
    slug = db.Column(db.String(80))
    type = db.Column(db.String(20), default="normal") # date|normal|day
    created = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # === Extra settings ===
    due_date = db.Column(db.DateTime)
    anonymous_allowed = db.Column(db.Boolean, default=True)
    public_listing = db.Column(db.Boolean, default=False)
    require_login = db.Column(db.Boolean, default=False)
    show_results = db.Column(db.String(20), default="complete") # summary|complete|never|summary_after_vote|complete_after_vote
    send_mail = db.Column(db.Boolean, default=False)
    one_vote_per_user = db.Column(db.Boolean, default=True)
    allow_comments = db.Column(db.Boolean, default=True)
    deleted = db.Column(db.Boolean, default=False)

    RESERVED_NAMES = ["login", "logout", "index", "user", "admin"]

    # relationships
    choices = db.relationship("Choice", backref="poll", cascade="all, delete-orphan", lazy="dynamic")
    choice_values = db.relationship("ChoiceValue", backref="poll", lazy="dynamic")
    watchers = db.relationship("PollWatch", backref="poll", cascade="all, delete-orphan", lazy="dynamic")
    comments = db.relationship("Comment", backref="poll", cascade="all, delete-orphan", lazy="dynamic")
    votes = db.relationship("Vote", backref="poll", cascade="all, delete-orphan", lazy="dynamic")

    _vote_choice_map = None
    _choices = None

    def __init__(self):
        self.created = datetime.utcnow()
        # create yes/no/maybe default choice values
        self.choice_values.append(ChoiceValue("yes", "check", "9C6", 1.0))
        self.choice_values.append(ChoiceValue("no", "ban", "F96", 0.0))
        self.choice_values.append(ChoiceValue("maybe", "question", "FF6", 0.5))

    @property
    def is_expired(self):
        return self.due_date and self.due_date < datetime.utcnow()

    def show_votes(self, user):
        return self.user_can_administrate(user) \
            or self.show_results == "complete" \
            or (self.show_results == "complete_after_vote" and self.is_expired)

    def show_summary(self, user):
        return self.user_can_administrate(user) \
            or self.show_votes \
            or self.show_results == "summary" \
            or (self.show_results == "summary_after_vote" and self.is_expired)

    @property
    def has_choices(self):
        return len(self.get_choices()) > 0

    def get_url(self):
        return url_for("poll", slug=self.slug)

    def get_vote_choice(self, vote, choice):
        if not self._vote_choice_map:
            self._vote_choice_map = {vote: {vote_choice.choice: vote_choice for vote_choice in vote.vote_choices} for vote in self.votes}

        try:
            return self._vote_choice_map[vote][choice]
        except KeyError:
            return None
        # return VoteChoice.query.filter_by(vote=vote, choice=choice).first()

    def get_choices(self):
        if self._choices == None:
            self._choices = Choice.query.filter_by(poll_id=self.id, deleted=False).all()
            self._choices.sort(key=Choice.get_hierarchy)
            print([c.get_hierarchy() for c in self._choices])
        return self._choices

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

    def user_can_administrate(self, user):
        return (user and user.is_authenticated() and (self.author == user or user.is_admin))

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
            hierarchy = choice.get_hierarchy()

            group = groups
            for part in hierarchy[:-1]:
                if not part in group:
                    group[part] = {}
                group = group[part]
            group[hierarchy[-1]] = choice

        return groups

    def choice_groups_valid(self):
        # try if grouping works correctly, this is hacky but okay :D
        try:
            self.get_choice_groups()
            return True
        except TypeError:
            return False

    # Weird algorithm. Required for poll.html and vote.html
    def get_choice_group_matrix(self):
        matrix = [choice.get_hierarchy() for choice in self.get_choices()]
        matrix = [[[item, 1, 1] for item in row] for row in matrix]
        width = max(len(row) for row in matrix)

        def fill(row, length):
            if len(row) >= length: return
            row.append([None, 1, 1])
            fill(row, length)

        for row in matrix:
            fill(row, width)

        # Merge None left to determine depth
        for i in range(width-1, 0, -1):
            for row in matrix:
                if row[i][0] == None:
                    row[i-1][1] = row[i][1] + 1

        # Merge items up and replace by None
        for i in range(len(matrix)-1, 0, -1):
            for j in range(width):
                if matrix[i][j][0] == matrix[i-1][j][0]:
                    matrix[i-1][j][2] = matrix[i][j][2] + 1
                    matrix[i][j][0] = None

        # cut off time column in day mode, only use date field
        if self.type == "day":
            matrix = [[row[0]] for row in matrix]

        return matrix


    def get_choices_by_group(self, group):
        return [choice for choice in self.get_choices() if choice.group == group]

    def get_comments(self):
        return Comment.query.filter_by(poll=self, deleted=False).order_by(db.asc(Comment.created)).all()

    def fill_vote_form(self, form):
        while form.vote_choices:
            form.vote_choices.pop_entry()

        for choice in self.get_choices():
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
            totals[choice] = choice.vote_choices.count()
            scores[choice] = 0
            for value, count in choice_counts.items():
                scores[choice] += count * value.weight

        max_score = max(scores.values())

        return scores, counts, totals, max_score

    def is_watching(self, user):
        return PollWatch.query.filter_by(poll=self, user=user).first()

    def send_watchers(self, subject, template, **kwargs):
        with mail.record_messages() as outbox:
            with mail.connect() as conn:
                for watcher in self.watchers:
                    user = watcher.user
                    msg = Message(recipients=[user.email], subject=subject,
                                  body=render_template(template, poll=self, user=user, **kwargs))
                    conn.send(msg)

            for m in outbox:
                print(m.subject)
                print("===========================")
                print(m.body)
                print("===========================")

    def to_dict(self):
        dictify = lambda l, f=(lambda x: True): {i.id: i.to_dict() for i in l if f(i)}

        return dict(choices=dictify(self.choices, lambda c: not c.deleted),
            choice_values=dictify(self.choice_values, lambda c: not c.deleted),
            votes=dictify(self.votes),
            comments=dictify(self.comments, lambda c: not c.deleted),
            choice_groups=[[choice.id for choice in group] for group in self.get_choice_groups()])

    def should_auto_delete(self):
        now = datetime.utcnow() + timedelta(days=100)

        # should live at least 30 days
        threshold_created = 30
        if now < self.created + timedelta(days=threshold_created):
            return False

        # should live at least 30 days after deadline
        threshold_deadline = 30
        if self.due_date and now < self.due_date + timedelta(days=threshold_created):
            return False

        # should live at least 60 days after last vote
        threshold_lastvote = 60
        votedates = [vote.created for vote in self.votes]
        if votedates:
            votedate = max(votedates)
            if votedate and now < votedate + timedelta(days=threshold_lastvote):
                return False

        # should live at least 30 days after last comment
        threshold_lastcomment = 30
        commentdates = [comment.created for comment in self.comments]
        if commentdates:
            commentdate = max(commentdate)
            if commentdate and now < commentdate + timedelta(days=threshold_lastvote):
                return False

        return True

