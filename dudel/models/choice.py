from dudel import db

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

    # relationships
    vote_choices = db.relationship("VoteChoice", backref="choice", lazy="dynamic")

    def __cmp__(self,other):
        return cmp(self.date, other.date) or cmp(self.deleted, other.deleted) or cmp(self.text, other.text)

    def get_counts(self):
        counts = {vc: 0 for vc in self.poll.choice_values}
        for vote_choice in self.vote_choices:
            if vote_choice.value:
                counts[vote_choice.value] += 1
        return counts

    @property
    def group(self):
        if self.date:
            return self.date.date()
        else:
            return "default" # normal polls only have one default group

    def to_dict(self):
        return dict(id=self.id, 
            text=self.text, 
            date=str(self.date),
            deleted=self.deleted)