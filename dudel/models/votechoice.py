from dudel import db

class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    value_id = db.Column(db.Integer, db.ForeignKey("choice_value.id"))
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
