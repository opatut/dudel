from dudel import db
from uuid import uuid4
from datetime import datetime, timedelta

class AccessToken(db.Model):
    id = db.Column(db.String(40), primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    scope = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    @classmethod
    def generate(cls, user, application=None, scope=None, ttl=3600):
        return AccessToken(
                id=str(uuid4()),
                application_id=application.id if hasattr(application, 'id') else application,
                user_id=user.id if hasattr(user, 'id') else user,
                scope=scope,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl),
        )
