from dudel import db

class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    value = db.relationship("ChoiceValue", backref="vote_choices")
    value_id = db.Column(db.Integer, db.ForeignKey("choice_value.id"))
    vote = db.relationship("Vote", backref="vote_choices")
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice = db.relationship("Choice", backref="vote_choices")
    choice_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
