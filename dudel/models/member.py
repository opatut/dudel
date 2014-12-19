from dudel import db

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(20), default="manual") # ldap|manual
    type = db.Column(db.String(10))

    polls = db.relationship("Poll", backref="owner", lazy="dynamic")

    __mapper_args__ = {
        'polymorphic_identity':'member',
        'polymorphic_on':type
    }
