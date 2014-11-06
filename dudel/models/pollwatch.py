from dudel import db

class PollWatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll = db.relationship("Poll", backref="watchers")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    user = db.relationship("User", backref="watches")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, poll, user):
        self.poll = poll
        self.user = user
