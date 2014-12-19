from dudel import db
from datetime import datetime

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    anonymous = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime)
    comment = db.Column(db.Text)

    def __init__(self):
        self.created = datetime.utcnow()

    # relationship
    vote_choices = db.relationship("VoteChoice", backref="vote", cascade="all, delete-orphan", lazy="dynamic")

    def user_can_delete(self, user):
        # disallow on deleted/expired polls
        if self.poll.deleted or self.poll.is_expired: return False
        # only if logged in
        if not user.is_authenticated(): return False
        # allow for poll author
        if self.poll.user_can_administrate(user): return True
        # allow for user
        if self.user and self.user == user: return True
        # allow for admin
        if user.is_admin: return True
        # disallow
        return False

    def user_can_edit(self, user):
        # disallow on deleted/expired polls
        if self.poll.deleted or self.poll.is_expired: return False
        # allow for poll author
        if self.poll.user_can_administrate(user): return True
        # allow for admin
        if user.is_authenticated() and user.is_admin: return True
        # allow for creator
        if self.user: return user == self.user
        # allow everyone, if no creator
        return True

    @property
    def displayname(self):
        return ("anonymous" if self.anonymous else (self.user.displayname if self.user else (self.name or "unknown")))

    def to_dict(self):
        return dict(id=self.id,
            displayname=self.displayname,
            name=self.name if not self.anonymous else None,
            user_id=self.user_id if not self.anonymous else 0,
            vote_choices={vc.id: vc.to_dict() for vc in self.vote_choices},
            anonymous=self.anonymous)
