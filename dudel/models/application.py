from dudel import db

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(64), unique=True)
    client_secret = db.Column(db.String(64))
    title = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    scope = db.Column(db.Text)
    redirect_url = db.Column(db.String(255))

    access_tokens = db.relationship("AccessToken", backref="application", cascade="all, delete-orphan", lazy="dynamic")
