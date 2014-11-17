from dudel import db

class PollWatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, poll, user):
        self.poll = poll
        self.user = user
