from flask import render_template
from flask.ext.babel import lazy_gettext

from dudel import db, gravatar


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    name = db.Column(db.String(80))
    type = db.Column(db.String(40))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    __mapper_args__ = {
        'polymorphic_identity': 'activity',
        'polymorphic_on': type
    }

    def get_user_link(self):
        if self.user:
            return self.user.displayname
        elif self.name:
            return self.name
        else:
            return lazy_gettext("someone")

    def get_avatar(self, size):
        if self.user:
            return self.user.get_avatar(size)
        else:
            return gravatar(self.name, size)


    def render(self, group):
        # TODO: sanitize path
        return render_template("activity/" + self.type + ".jade", activity=self, group=group)


class VoteCreatedActivity(Activity):
    id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    vote_id = db.Column(db.Integer, db.ForeignKey('vote.id'))

    __mapper_args__ = {
        'polymorphic_identity': 'vote_created'
    }


class Comment(Activity):
    id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    text = db.Column(db.Text)
    deleted = db.Column(db.Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'comment'
    }

    def user_can_edit(self, user):
        if not self.user: return True
        if user.is_anonymous(): return False
        if user.is_admin: return True
        return user == self.user or user == self.poll.user_can_administrate(user)

    def render(self, group):
        if group != [self]:
            raise ValueError("Comment should not be rendered as an activity group.")

        return render_template("activity/comment.jade", activity=self)
