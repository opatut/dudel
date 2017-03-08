from flask import render_template
from flask_login import current_user, login_required

from dudel import app, db
from dudel.models import Poll, User, Group, PollType
from dudel.filters import cx

@app.route("/admin/")
@login_required
def admin_index():
    current_user.require_admin()
    polls = Poll.query.order_by(db.desc(Poll.created)).limit(5)
    users = User.query.order_by(db.desc(User.id)).limit(5)
    return render_template("admin/index.jade", polls=polls, users=users)


@app.route("/admin/polls/")
@login_required
def admin_polls():
    current_user.require_admin()
    polls = Poll.query.order_by(db.desc(Poll.created)).all()
    return render_template("admin/polls.jade", polls=polls)


@app.route("/admin/poll/<int:id>/")
@login_required
def admin_poll(id):
    current_user.require_admin()
    poll = Poll.query.filter_by(id=id).first_or_404()
    return render_template("admin/poll.jade", poll=poll)


@app.route("/admin/users/")
@login_required
def admin_users():
    current_user.require_admin()
    users = User.query.order_by(db.asc(User.username)).all()
    return render_template("admin/users.jade", users=users)


@app.route("/admin/groups/")
@login_required
def admin_groups():
    current_user.require_admin()
    groups = Group.query.order_by(db.asc(Group.name)).all()
    return render_template("admin/groups.jade", groups=groups)


@app.route("/admin/user/<int:id>/")
@login_required
def admin_user(id):
    current_user.require_admin()
    user = User.query.filter_by(id=id).first_or_404()
    return render_template("admin/user.jade", user=user)
