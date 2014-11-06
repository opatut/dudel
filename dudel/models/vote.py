from dudel import db

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    poll = db.relationship("Poll", backref="votes")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    user = db.relationship("User", backref="votes")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    anonymous = db.Column(db.Boolean, default=False)

    def user_can_delete(self, user):
        # only if logged in
        if not user.is_authenticated(): return False
        # allow for poll author 
        if self.poll.author and self.poll.author == user: return True
        # allow for user
        if self.user and self.user == user: return True
        # allow for admin
        if user.is_admin: return True
        # disallow
        return False

    def user_can_edit(self, user):
        # allow for author
        if self.poll.author and self.poll.author == user: return True
        # allow for admin
        if user.is_authenticated() and user.is_admin: return True
        # allow for creator
        if self.user: return user == self.user
        # allow everyone, if no creator
        return True

    @property
    def displayname(self):
        return ("anonymous" if self.anonymous else (self.user.displayname if self.user else (self.name or "unknown")))
