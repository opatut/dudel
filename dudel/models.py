from dudel import app, db

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    slug = db.Column(db.String(80))
    due_date = db.Column(db.DateTime)
    type = db.Column(db.Enum("date", "normal"), default="normal")

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    poll = db.relationship("Poll", backref="choices")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    poll = db.relationship("Poll", backref="votes")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))

class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vote = db.relationship("Vote", backref="vote_choices")
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice = db.relationship("Choice", backref="vote_choices")
    choide_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
