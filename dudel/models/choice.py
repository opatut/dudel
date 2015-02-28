from dudel import db
from dudel.util import PartialDateTime, DateTimePart
from datetime import datetime

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

    # relationships
    vote_choices = db.relationship("VoteChoice", backref="choice", lazy="dynamic")

    def __init__(self, content=None, poll=None):
        if content:
            if isinstance(content, str):
                self.text = content
            elif isinstance(content, datetime):
                self.date = content
            else:
                raise ValueError("Invalid content type for choice: %s" % type(content))

        if poll:
            self.poll = poll

    def __cmp__(self,other):
        return cmp(self.date, other.date) or cmp(self.deleted, other.deleted) or cmp(self.text, other.text)

    def get_counts(self):
        counts = {vc: 0 for vc in self.poll.choice_values}
        for vote_choice in self.vote_choices:
            if vote_choice.value:
                counts[vote_choice.value] += 1
        return counts

    def get_hierarchy(self):
        if self.date:
            return [PartialDateTime(self.date, DateTimePart.date, self.poll.localization_context),
                PartialDateTime(self.date, DateTimePart.time, self.poll.localization_context)]
        else:
            return [part.strip() for part in self.text.split("/") if part]

    def to_dict(self):
        return dict(id=self.id,
            text=self.text,
            date=str(self.date),
            deleted=self.deleted)

    @property
    def title(self):
        from dudel.filters import date, datetime
        from dudel.models.poll import PollType

        if self.poll.type == PollType.date:
            return date(self.date, ref=self.poll)
        elif self.poll.type == PollType.datetime:
            return datetime(self.date, ref=self.poll.localization_context)
        else:
            return '<i class="fa fa-chevron-right choice-separator"></i>'.join(self.get_hierarchy())
            # return self.text

    @property
    def value(self):
        from dudel.models.poll import PollType

        if self.poll.type == PollType.date:
            return PartialDateTime(self.date, DateTimePart.date, self.poll.localization_context)
        elif self.poll.type == PollType.datetime:
            return self.date
        else:
            return self.text

    def copy(self):
        n = Choice()
        n.text = self.text
        n.date = self.date
        n.poll = self.poll
        n.deleted = self.deleted
        return n
