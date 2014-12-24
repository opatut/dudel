from dudel import db
from datetime import datetime

class PollInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    created = db.Column(db.DateTime)

    def __init__(self):
        self.created = datetime.utcnow()

    @property
    def voted(self):
        return self.vote != None
