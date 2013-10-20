from dudel import app, db
from dudel.models import *
from dudel.forms import *
from flask import redirect, abort, request, render_template, flash, url_for
from dateutil import parser

@app.route("/", methods=("POST", "GET"))
def index():
    form = CreatePollForm()
    if form.validate_on_submit():
        poll = Poll()
        form.populate_obj(poll)
        db.session.add(poll)
        db.session.commit()
        flash("Poll created")
        return redirect(poll.get_url())

    polls = Poll.query.all()

    return render_template("index.html", polls=polls, form=form)

@app.route("/<slug>")
def poll(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    return render_template("poll.html", poll=poll)

@app.route("/<slug>/edit/", methods=("POST", "GET"))
def poll_edit(slug, step=1):
    return "edit"

@app.route("/<slug>/choices/", methods=("POST", "GET"))
@app.route("/<slug>/choices/<int:step>", methods=("POST", "GET"))
def poll_edit_choices(slug, step=1):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    args = {}

    if poll.type == "date":
        if step == 1:
            # Put dates into session
            if not "dates" in session.keys(): session["dates"] = {}
            if not poll.slug in session["dates"]: session["dates"][poll.slug] = poll.get_choice_dates()

            # Put times into session
            if not "times" in session.keys(): session["times"] = {}
            if not poll.slug in session["times"]: session["times"][poll.slug] = poll.get_choice_times()

            date_form = AddDateForm()
            if date_form.validate_on_submit():
                date = str(date_form.date.data)
                if date in session["dates"][poll.slug]:
                    session["dates"][poll.slug].remove(date)
                else:
                    session["dates"][poll.slug].append(date)
            args["date_form"] = date_form

            time_form = AddTimeForm()
            if time_form.validate_on_submit():

                time = str(parser.parse("2013-01-01 " + time_form.time.data, fuzzy=True).time())
                print("Time submitted %s" % time)
                if time in session["times"][poll.slug]:
                    session["times"][poll.slug].remove(time)
                else:
                    session["times"][poll.slug].append(time)
            args["time_form"] = time_form

        if step == 1 or step == 2:
            # parse dates from session, fill with choices
            args["dates"] = [parser.parse(data, fuzzy=True).date() for data in session["dates"][poll.slug]]
            args["times"] = [parser.parse(data, fuzzy=True).time() for data in session["times"][poll.slug]]

        if step == 2 and request.method == "POST":
            # list all date/time combinations
            datetimes = [parser.parse(data) for data in request.form.getlist("datetimes[]")]
            existing_datetimes = [choice.date for choice in poll.choices]

            # disable all that are not listed
            for choice in poll.choices:
                choice.deleted = not choice.date in datetimes
                print("Setting datetime %s to deleted: %s" % (choice.date, choice.deleted))

            # create those that don't exist yet
            for datetime in datetimes:
                if not datetime in existing_datetimes:
                    choice = Choice()
                    choice.date = datetime
                    poll.choices.append(choice)
                    print("Adding datetime %s" % datetime)
                    db.session.add(choice)

            db.session.commit()
            flash("The choices list has been updated.", "success")
            return redirect(poll.get_url())

    return render_template("poll_edit_choices.html", poll=poll, step=step, **args)

@app.route("/<slug>/vote")
def poll_vote(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    return render_template("vote.html", poll=poll)
