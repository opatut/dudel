from dudel import app, db
from dudel.models import *
from dudel.forms import *
from flask import redirect, abort, request, render_template, flash, url_for

@app.route("/", methods=("POST", "GET"))
def index():
    form = CreatePollForm()
    if form.validate_on_submit():
        poll = Poll()
        form.populate_obj(poll)
        db.session.add(poll)
        db.session.commit()
        flash("Poll created")
        return redirect(url_for("index"))

    polls = Poll.query.all()

    return render_template("index.html", polls=polls, form=form)
