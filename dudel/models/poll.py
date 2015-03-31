from datetime import datetime, timedelta

import hmac

from enum import Enum

from flask import url_for, render_template
from flask.ext.babel import lazy_gettext
from flask.ext.login import current_user
from flask.ext.mail import Message

from pytz import timezone

from enum import Enum

from dudel import db, mail, app
from dudel.models.choice import Choice
from dudel.models.choicevalue import ChoiceValue
from dudel.models.activity import Comment
from dudel.models.pollwatch import PollWatch
from dudel.models.vote import Vote
from dudel.models.invitation import Invitation
from dudel.util import PollExpiredException, PollActionException, LocalizationContext


class PollType(str, Enum):
    datetime = "date"
    date = "day"
    normal = "normal"
    numeric = "numeric"

    @property
    def icon(self):
        return {
            PollType.datetime: "clock-o",
            PollType.date:     "calendar",
            PollType.normal:   "list",
            PollType.numeric:  "sliders"
        }[self]

    @property
    def title(self):
        return {
            PollType.datetime: lazy_gettext("Date and Time"),
            PollType.date:     lazy_gettext("Date"),
            PollType.normal:   lazy_gettext("Normal Poll"),
            PollType.numeric:  lazy_gettext("Numeric")
        }[self]

    @property
    def description(self):
        return {
            PollType.datetime: lazy_gettext("Schedule date and time for an event"),
            PollType.date:     lazy_gettext("Schedule an all-day event"),
            PollType.normal:   lazy_gettext("Retrieve opinions on various choices"),
            PollType.numeric:  lazy_gettext("Rate each choice in a numeric range")
        }[self]

    def __str__(self):
        return str(self.title)


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    description = db.Column(db.Text)
    slug = db.Column(db.String(80))
    type = db.Column(db.String(20), default="normal") # PollType
    created = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey("member.id"))

    # === Extra settings ===
    due_date = db.Column(db.DateTime)
    anonymous_allowed = db.Column(db.Boolean, default=True)
    public_listing = db.Column(db.Boolean, default=False)
    require_login = db.Column(db.Boolean, default=False)
    require_invitation = db.Column(db.Boolean, default=False)
    show_results = db.Column(db.String(20), default="complete") # summary|complete|never|summary_after_vote|complete_after_vote
    send_mail = db.Column(db.Boolean, default=False)
    one_vote_per_user = db.Column(db.Boolean, default=True)
    allow_comments = db.Column(db.Boolean, default=True)
    deleted = db.Column(db.Boolean, default=False)
    show_invitations = db.Column(db.Boolean, default=True)
    timezone_name = db.Column(db.String(40))

    # Type: numeric
    amount_minimum = db.Column(db.Float, default=0)
    amount_maximum = db.Column(db.Float, default=None)
    amount_step = db.Column(db.Float, default=1)

    RESERVED_NAMES = ["login", "logout", "index", "user", "admin", "api", "register", "static"]

    # relationships
    choices = db.relationship("Choice", backref="poll", cascade="all, delete-orphan", lazy="dynamic")
    choice_values = db.relationship("ChoiceValue", backref="poll", lazy="dynamic")
    watchers = db.relationship("PollWatch", backref="poll", cascade="all, delete-orphan", lazy="dynamic")
    activities = db.relationship("Activity", backref="poll", cascade="all, delete-orphan", lazy="dynamic")
    votes = db.relationship("Vote", backref="poll", cascade="all, delete-orphan", lazy="dynamic")
    invitations = db.relationship("Invitation", backref="poll", cascade="all, delete-orphan", lazy="dynamic")

    _vote_choice_map = None
    _choices = None

    def __init__(self, title=None, slug=None, type=None, create_choice_values=True):
        if title:
            self.title = title

        if slug:
            self.slug = slug

        if type:
            self.type = type

        self.created = datetime.utcnow()

        # create yes/no/maybe default choice values
        if create_choice_values:
            self.choice_values.append(ChoiceValue("yes", "check", "9C6", 1.0))
            self.choice_values.append(ChoiceValue("no", "ban", "F96", 0.0))
            self.choice_values.append(ChoiceValue("maybe", "question", "FF6", 0.5))

    @property
    def comments(self):
        return self.activities.filter_by(type="comment")

    @property
    def is_expired(self):
        return self.due_date and self.due_date < datetime.utcnow()

    def numeric_format(self, extra_digits=0):
        if not self.type == PollType.numeric:
            raise TypeError("Poll %s is not of type numeric." % self.slug)

        def get_decimal_places(val):
            decimals = str(val).rstrip("0").split(".")
            return len(decimals[1]) if (len(decimals) > 1) else 0

        return "%%.%df" % (max(map(get_decimal_places, [self.amount_step, self.amount_maximum, self.amount_minimum])) + extra_digits)

    def invite(self, user):
        result = True
        invitation = Invitation.query.filter_by(poll_id=self.id, user_id=user.id).first()
        if invitation:
            return False

        invitation = Invitation()
        invitation.user = user
        invitation.poll = self
        if current_user.is_authenticated():
            invitation.creator = current_user

        vote = Vote.query.filter_by(poll_id=self.id, user_id=user.id).first()
        if vote:
            # create an invitation, just to track them
            invitation.vote = vote
            result = False

        db.session.add(invitation)
        invitation.send_mail()
        return result

    def invite_all(self, users):
        invited = []
        failed = []

        users = list(set(users))

        for user in users:
            if not user: continue
            if self.invite(user):
                invited.append(user)
            else:
                failed.append(user)

        return invited, failed

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

    def get_url(self, subpage=None, **kwargs):
        return url_for("poll" + (("_%s" % subpage) if subpage else ""), slug=self.slug, **kwargs)

    def get_vote_choice(self, vote, choice):
        if not self._vote_choice_map:
            self._vote_choice_map = {vote: {vote_choice.choice: vote_choice for vote_choice in vote.vote_choices} for vote in self.votes}

        try:
            return self._vote_choice_map[vote][choice]
        except KeyError:
            return None
        # return VoteChoice.query.filter_by(vote=vote, choice=choice).first()

    def get_choices(self):
        if self._choices is None:
            self._choices = Choice.query.filter_by(poll_id=self.id, deleted=False).all()
            self._choices.sort(key=Choice.get_hierarchy)
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
        # Owners may administrate
        if self.owner and user.is_authenticated() and user.is_member(self.owner): return True
        # Admins may administrate
        if (user.is_authenticated() and user.is_admin): return True
        # Everyone else may not
        return False

    def user_can_edit(self, user):
        # If no owner is set, everyone may edit
        if not self.owner: return True
        # Owners may edit
        if user.is_authenticated() and user.is_member(self.owner): return True
        # Admins may edit
        if user.is_authenticated() and user.is_admin: return True
        # Everyone else may not
        return False

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

    def choice_groups_valid(self, left_hierarchy, ignore_id=None):
        for right in self.get_choices():
            if ignore_id is not None and right.id == ignore_id:
                continue
            right_hierarchy = right.get_hierarchy()
            smaller = min([len(left_hierarchy), len(right_hierarchy)])
            if left_hierarchy[:smaller] == right_hierarchy[:smaller]:
                return False
        return True

    # Weird algorithm. Required for poll.jade and vote.jade
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
                if row[i][0] is None:
                    row[i-1][1] = row[i][1] + 1

        # Merge items up and replace by None
        for i in range(len(matrix)-1, 0, -1):
            for j in range(width):
                if matrix[i][j][0] == matrix[i-1][j][0] and matrix[i][j][1] == matrix[i-1][j][1]:
                    matrix[i-1][j][2] = matrix[i][j][2] + 1
                    matrix[i][j][0] = None

        # cut off time column in day mode, only use date field
        if self.type == PollType.date:
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
        if self.type == PollType.numeric:
            totals = {}
            counts = {}
            averages = {}

            for choice in self.choices:
                amounts = [vote_choice.amount for vote_choice in choice.vote_choices]
                counts[choice] = len(amounts)
                totals[choice] = sum(amounts)
                averages[choice] = totals[choice] / counts[choice] if amounts else 0

            return totals, counts, averages

        else:
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

    @property
    def last_changed(self):
        dates = []
        dates.append(self.created)

        if self.due_date:
            dates.append(self.due_date)

        for vote in self.votes:
            dates.append(vote.created)

        for activity in self.activities:
            dates.append(activity.created)

        dates = [date for date in dates if date]

        return max(dates)

    @property
    def timezone(self):
        return timezone(self.timezone_name) if self.timezone_name else None

    @property
    def localization_context(self):
        return LocalizationContext(current_user, self)

    @property
    def should_auto_delete(self):
        return self.last_changed + timedelta(days=60) < datetime.utcnow()

    def get_choice_range(self):
        values = [choice.value for choice in self.get_choices()]
        if not values: return None, None
        out = min(values), max(values)
        if self.type == PollType.datetime:
            out = [v.datetime for v in out]
        return out

    def get_mac(self, user_id=None):
        """
        Generates a mac for actions on a poll

        :param user_id: The id from the user the mac is for. If it is None the current_user.id is used
        :return: String
        """
        if not user_id:
            user_id = current_user.id
        to_sign = '{}/{}'.format(self.slug, user_id)
        return hmac.new(app.config['SECRET_KEY'], to_sign).hexdigest()

    def post_activity(self, activity, user=None):
        activity.poll = self
        activity.created = datetime.utcnow()

        if user:
            if isinstance(user, str) or isinstance(user, unicode):
                activity.name = user
            elif user and hasattr(user, 'is_authenticated') and user.is_authenticated():
                activity.user = user
            else:
                print("No idea what to make of", user)
        elif current_user.is_authenticated():
            activity.user = current_user

        db.session.add(activity)

    def get_activity_groups(self, ref=current_user):
        activities = self.activities.order_by('created DESC')

        from dudel.filters import in_timezone_of

        mergeable = ['vote_created']
        groups = []

        for activity in activities:

            # create a new group
            if (not groups) or \
                (activity.type not in mergeable) or \
                (groups[-1][0].type != activity.type) or \
                (in_timezone_of(groups[-1][0].created, ref).date() != in_timezone_of(activity.created, ref).date()):

                groups.append([])

            groups[-1].append(activity)

        return groups
