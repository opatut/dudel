from dudel import db


class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    value_id = db.Column(db.Integer, db.ForeignKey("choice_value.id"))
    amount = db.Column(db.Float)
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice_id = db.Column(db.Integer, db.ForeignKey("choice.id"))

    def to_dict(self):
        return dict(id=self.id,
            comment=self.comment,
            value_id=self.value_id,
            vote_id=self.vote_id,
            choice_id=self.choice_id)