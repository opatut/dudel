from dudel import db

class AccessToken(db.Model):
    id = db.Column(db.String(40), primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    scope = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    def __str__(self):
        return 'Bearer {}'.format(self.id)

    @property
    def attributes(self):
        return [('scope', '*' if self.scope is None else self.scope)]


