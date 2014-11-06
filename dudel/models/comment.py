from dudel import db

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
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
