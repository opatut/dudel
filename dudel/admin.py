from dudel import app, db
from dudel.models import *
from dudel.forms import *
from flask import redirect, abort, request, render_template, flash, url_for, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from dateutil import parser
from datetime import datetime

@app.route("/admin/")
@login_required
def admin_index():
    current_user.require_admin()
    polls = Poll.query.order_by(db.desc(Poll.created)).limit(5)
    users = User.query.limit(5)
    return render_template("admin/index.html", polls=polls, users=users)

@app.route("/admin/polls/")
@login_required
def admin_polls():
    current_user.require_admin()
    polls = Poll.query.order_by(db.desc(Poll.created)).all()
    return render_template("admin/polls.html", polls=polls)

@app.route("/admin/poll/<int:id>/")
@login_required
def admin_poll(id):
    current_user.require_admin()
    poll = Poll.query.filter_by(id=id).first_or_404()
    return render_template("admin/poll.html", poll=poll)

@app.route("/admin/users/")
@login_required
def admin_users():
    current_user.require_admin()
    users = User.query.order_by(db.asc(User.username)).all()
    return render_template("admin/users.html", users=users)

@app.route("/admin/user/<int:id>/")
@login_required
def admin_user(id):
    current_user.require_admin()
    user = User.query.filter_by(id=id).first_or_404()
    return render_template("admin/user.html", user=user)
