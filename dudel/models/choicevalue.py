from dudel import db


class ChoiceValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    icon = db.Column(db.String(64))
    color = db.Column(db.String(6))
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Float, default=0.0)

    # relationships
    vote_choices = db.relationship("VoteChoice", backref="value", lazy="dynamic")

    def __init__(self, title="", icon="question", color="EEEEEE", weight=0.0):
        self.title = title
        self.icon = icon
        self.color = color
        self.weight = weight

    def to_dict(self):
        return dict(id=self.id,
                    title=self.title,
                    icon=self.title,
                    color=self.color,
                    deleted=self.deleted,
                    weight=self.weight)

    def copy(self):
        n = ChoiceValue()
        n.title = self.title
        n.icon = self.icon
        n.color = self.color
        n.deleted = self.deleted
        n.weight = self.weight
        n.poll = self.poll
        return n

