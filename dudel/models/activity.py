from flask import render_template
from flask.ext.babel import lazy_gettext

from dudel import db, gravatar


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(40))
    created = db.Column(db.DateTime)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    name = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    __mapper_args__ = { 'polymorphic_identity': 'activity', 'polymorphic_on': type }

    groupable = False
    notifiable = False

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
        return render_template("activity/%s.jade" % self.type, activity=self, group=group)


class PollCreatedActivity(Activity):
    id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    __mapper_args__ = { 'polymorphic_identity': 'poll_created' }


class VoteCreatedActivity(Activity):
    id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    vote_id = db.Column(db.Integer, db.ForeignKey('vote.id'))
    __mapper_args__ = { 'polymorphic_identity': 'vote_created' }
    groupable = True
    notifiable = True


choices_updated_added = db.Table('choices_updated_added', db.metadata,
    db.Column('choice_id', db.Integer, db.ForeignKey('choice.id')),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'))
)

choices_updated_removed = db.Table('choices_updated_removed', db.metadata,
    db.Column('choice_id', db.Integer, db.ForeignKey('choice.id')),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'))
)

class ChoicesUpdatedActivity(Activity):
    id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    __mapper_args__ = { 'polymorphic_identity': 'choices_updated' }
    choices_added = db.relationship("Choice", backref="added_in_activity", lazy="dynamic", secondary="choices_updated_added")
    choices_removed = db.relationship("Choice", backref="removed_in_activity", lazy="dynamic", secondary="choices_updated_removed")
    groupable = True #TODO
    notifiable = True

    def perform_grouping(self, group):
        added = []
        removed = []

        for a in reversed(group):
            for c in a.choices_added:
                if c in removed:
                    removed.remove(c)
                else:
                    added.append(c)
            for c in a.choices_removed:
                if c in added:
                    added.remove(c)
                else:
                    removed.append(c)

        return added, removed


class Comment(Activity):
    id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    text = db.Column(db.Text)
    deleted = db.Column(db.Boolean, default=False)
    __mapper_args__ = { 'polymorphic_identity': 'comment' }
    notifiable = True

    def user_can_edit(self, user):
        if not self.user: return True
        if user.is_anonymous(): return False
        if user.is_admin: return True
        return user == self.user or user == self.poll.user_can_administrate(user)

    def render(self, group):
        if group != [self]:
            raise ValueError("Comment should not be rendered as an activity group.")

        return render_template("activity/comment.jade", activity=self)
