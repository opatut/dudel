from dudel import app, db
from dudel.models import User, Poll, Vote, Choice, ChoiceValue, VoteChoice, get_user
from dudel.forms import CreatePollForm, EditPollForm, CreateVoteForm, DateTimeSelectForm, AddChoiceForm, AddValueForm, LoginForm
from flask import redirect, abort, request, render_template, flash, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
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
        return redirect(url_for("poll_edit_choices", slug=poll.slug))

    polls = Poll.query.filter_by(public_listing=True).all()

    poll_count = Poll.query.count()
    vote_count = Vote.query.count()
    user_count = User.query.count()

    return render_template("index.html", polls=polls, form=form, poll_count=poll_count, vote_count=vote_count, user_count=user_count)

@app.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = get_user(form.username.data)
        login_user(user)
        flash("You were logged in, %s." % user.displayname, "success")
        return redirect(url_for("index"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    flash("You were logged out, %s. Goodbye!" % current_user.displayname, "success")
    logout_user()
    return redirect(url_for("index"))

@app.route("/<slug>/")
def poll(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    # if poll.password_mode in ("show"):
    #     if not poll.has_password():
    #         return redirect(url_for("poll_password", slug=poll.slug, next=request.url))

    return render_template("poll.html", poll=poll)

@app.route("/<slug>/edit/", methods=("POST", "GET"))
def poll_edit(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    form = EditPollForm(obj=poll)

    # if poll.password_mode in ("edit"):
    #     if not poll.has_password():
    #         return redirect(url_for("poll_password", slug=poll.slug, next=request.url))
    # elif poll.password_mode in ("none"):
    #     pass #TODO

    if form.validate_on_submit():
        form.populate_obj(poll)
        db.session.commit()
        flash("Poll settings have been saved.", "success")
        #return redirect(poll.get_url())
        return redirect(url_for("poll_edit", slug=poll.slug))

    return render_template("poll_edit.html", poll=poll, form=form)

@app.route("/<slug>/claim/", methods=("POST", "GET"))
@login_required
def poll_claim(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    if poll.author:
        abort(403)

    # if poll.password_mode in ("edit"):
    #     if not poll.has_password():
    #         return redirect(url_for("poll_password", slug=poll.slug, next=request.url))

    poll.author = current_user
    db.session.commit()
    flash("You claimed this poll. Only you may edit it now.", "success")
    return redirect(url_for("poll_edit", slug=poll.slug))


@app.route("/<slug>/choices/", methods=("POST", "GET"))
@app.route("/<slug>/choices/<int:step>", methods=("POST", "GET"))
def poll_edit_choices(slug, step=1):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    args = {}

    # if poll.password_mode in ("edit"):
    #     if not poll.has_password():
    #         return redirect(url_for("poll_password", slug=poll.slug, next=request.url))

    if poll.type == "date":
        form = DateTimeSelectForm()
        args["form"] = form

        if step == 1:
            form.dates.data = ",".join(set(choice.date.strftime("%Y-%m-%d") for choice in poll.choices))
            form.times.data = ",".join(set(choice.date.strftime("%H:%M") for choice in poll.choices))

        if step in (2, 3) and form.validate_on_submit():
            dates = form.dates.data.split(",")
            times = form.times.data.split(",")
            args["dates"] = sorted(list(set(parser.parse(data, fuzzy=True).date() for data in dates)))
            args["times"] = sorted(list(set(parser.parse("1970-01-01 %s" % data, fuzzy=True).time() for data in times)))

        if step == 3 and form.validate_on_submit():
            # list all date/time combinations
            datetimes = [parser.parse(data) for data in request.form.getlist("datetimes[]")]
            existing_datetimes = [choice.date for choice in poll.choices]

            # disable all that are not listed
            for choice in poll.choices:
                choice.deleted = not choice.date in datetimes

            # create those that don't exist yet
            for datetime in datetimes:
                if not datetime in existing_datetimes:
                    choice = Choice()
                    choice.date = datetime
                    poll.choices.append(choice)
                    db.session.add(choice)

            db.session.commit()
            flash("The choices list has been updated.", "success")
            return redirect(poll.get_url())

    else:
        form = AddChoiceForm()

        if form.validate_on_submit():
            text = form.text.data.strip()
            choice = Choice.query.filter_by(poll_id=poll.id, text=text).first()
            if choice:
                choice.deleted = not choice.deleted
            else:
                choice = Choice()
                choice.text = form.text.data
                poll.choices.append(choice)
                db.session.add(choice)
            db.session.commit()
            flash("The choice was %s." % ("disabled" if choice.deleted else "added"), "success")
            return redirect(url_for("poll_edit_choices", slug=poll.slug))

        if "toggle" in request.args:
            tid = request.args.get("toggle")
            choice = Choice.query.filter_by(id=tid, poll_id=poll.id).first_or_404()
            choice.deleted = not choice.deleted
            db.session.commit()
            flash("The choice was %s." % ("disabled" if choice.deleted else "added"), "success")
            return redirect(url_for("poll_edit_choices", slug=poll.slug))

        args["form"] = form

    return render_template("poll_edit_choices.html", poll=poll, step=step, **args)

@app.route("/<slug>/values/", methods=("POST", "GET"))
def poll_edit_values(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    form = AddValueForm()
    if form.validate_on_submit():
        value = ChoiceValue()
        value.title = form.title.data
        value.icon = form.icon.data
        value.color = form.color.data.lstrip("#")
        value.poll = poll
        db.session.add(value)
        db.session.commit()
        flash("The choice value was added.", "success")
        return redirect(url_for("poll_edit_values", slug=poll.slug))

    return render_template("poll_edit_values.html", poll=poll, form=form)

# @app.route("/<slug>/password", methods=("POST", "GET"))
# def poll_password(slug):
#     next = request.args.get("next")

#     poll = Poll.query.filter_by(slug=slug).first_or_404()
#     form = PollPassword()

#     if poll.has_password():
#         return redirect(next)

#     if form.validate_on_submit():
#         if form.password.data == poll.password:
#             poll.set_password()
#             return redirect(next)
#         else:
#             flash("Incorrect password, try again!", "error")

#     return render_template("poll_password.html", poll=poll, next=next, form=form)

@app.route("/<slug>/vote", methods=("POST", "GET"))
def poll_vote(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    if poll.require_login and current_user.is_anonymous():
        return render_template("vote_error.html", reason="LOGIN_REQUIRED")

    # if poll.password_mode in ("show", "vote"):
    #     if not poll.has_password():
    #         return redirect(url_for("poll_password", slug=poll.slug, next=request.url))

    form = CreateVoteForm()

    if request.method == "POST":
        for subform in form.vote_choices:
            subform.value.choices = [(v.id, v.title) for v in poll.get_choice_values()]

        if form.validate_on_submit():
            vote = Vote()
            if current_user.is_anonymous():
                vote.name = form.name.data
            else:
                vote.user = current_user
            vote.anonymous = poll.anonymous_allowed and form.anonymous.data
            poll.votes.append(vote)

            for subform in form.vote_choices:
                choice = Choice.query.filter_by(id=subform.choice_id.data).first()
                value = ChoiceValue.query.filter_by(id=subform.value.data).first()
                if not choice or choice.poll != poll: abort(404)
                if value and value.poll != poll: abort(404)

                vote_choice = VoteChoice()
                vote_choice.value = value
                vote_choice.comment = subform.comment.data
                vote_choice.vote = vote
                vote_choice.choice = choice
                db.session.add(vote_choice)

            db.session.commit()
            return redirect(poll.get_url())

    if not request.method == "POST":
        poll.fill_vote_form(form)

    return render_template("vote.html", poll=poll, form=form)

@app.route("/<slug>/vote/<int:vote_id>/edit", methods=("POST", "GET"))
def poll_vote_edit(slug, vote_id):
    # TODO
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    vote = Vote.query.filter_by(id=vote_id).first_or_404()
    if vote.poll != poll: abort(404)

    form = CreateVoteForm(obj=vote)
    if poll.require_login and current_user.is_anonymous():
        return render_template("vote_error.html", reason="LOGIN_REQUIRED")

    if request.method == "POST":
        for subform in form.vote_choices:
            subform.value.choices = [(v.id, v.title) for v in poll.get_choice_values()]

        if form.validate_on_submit():
            if current_user.is_anonymous():
                vote.name = form.name.data
            vote.anonymous = poll.anonymous_allowed and form.anonymous.data

            for subform in form.vote_choices:
                choice = Choice.query.filter_by(id=subform.choice_id.data).first()
                value = ChoiceValue.query.filter_by(id=subform.value.data).first()
                if not choice or choice.poll != poll: abort(404)
                if value and value.poll != poll: abort(404)

                vote_choice = poll.get_vote_choice(vote, choice)
                vote_choice.comment = subform.comment.data
                vote_choice.value = value
                print("Set vote choice of %s to %s" % (choice, value.title))

            db.session.commit()
            flash("The vote has been edited.", "success")
            return redirect(poll.get_url())

    if not request.method == "POST":
        poll.fill_vote_form(form)

    return render_template("vote.html", poll=poll, form=form, vote=vote)
