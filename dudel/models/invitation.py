from dudel import db, mail
from datetime import datetime
from flask_mail import Message
from flask_babel import gettext
from flask import render_template


class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    created = db.Column(db.DateTime)

    def __init__(self):
        self.created = datetime.utcnow()

    @property
    def voted(self):
        return self.vote is not None

    def send_mail(self, reminder=False):
        # Do nothing if user opted out
        if not self.user.allow_invitation_mails: return

        template = "email/invitation.txt"
        if reminder:
            template = "email/invitation_reminder.txt"

        subject = gettext("[Dudel] Poll Invitation: %(title)s", title=self.poll.title)

        # For debugging
        with mail.record_messages() as outbox:
            with mail.connect() as conn:
                content = render_template(template, poll=self.poll, invitation=self, user=self.user)
                msg = Message(recipients=[self.user.email], subject=subject, body=content)
                conn.send(msg)

            for m in outbox:
                print("===========================")
                print("EMAIL SENT // " + m.subject)
                print(m.body)
                print("===========================")
