from dudel import app, db
from flask import url_for, session

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    slug = db.Column(db.String(80))
    due_date = db.Column(db.DateTime)
    type = db.Column(db.Enum("date", "normal"), default="normal")

    def get_url(self):
        return url_for("poll", slug=self.slug)

    def get_vote_choice(self, vote, choice):
        return VoteChoice.query.filter_by(vote=vote, choice=choice).first()

    def get_choices(self):
        return Choice.query.filter_by(poll_id=self.id).all()

    def get_choice_dates(self):
        return list(set([choice.date.date for choice in self.choices]))

    def get_choice_times(self):
        return list(set([choice.date.time for choice in self.choices]))

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    poll = db.relationship("Poll", backref="choices")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    poll = db.relationship("Poll", backref="votes")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))

class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notice = db.Column(db.String(64))
    value = db.Column(db.Enum("yes", "no", "maybe"), default="no")
    vote = db.relationship("Vote", backref="vote_choices")
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice = db.relationship("Choice", backref="vote_choices")
    choide_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
