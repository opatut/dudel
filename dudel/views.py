from dudel import app, db
from dudel.models import User, Poll, Vote, Choice, ChoiceValue, VoteChoice, get_user, Comment
from dudel.forms import CreatePollForm, EditPollForm, CreateVoteForm, DateTimeSelectForm, AddChoiceForm, EditChoiceForm, AddValueForm, LoginForm, CommentForm
from flask import redirect, abort, request, render_template, flash, url_for, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from dateutil import parser
from datetime import datetime

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
    if current_user.is_authenticated():
        user_polls = Poll.query.filter_by(author=current_user).all()
    else:
        user_polls = None

    poll_count = Poll.query.count()
    vote_count = Vote.query.count()
    user_count = User.query.count()

    return render_template("index.html", polls=polls, form=form, poll_count=poll_count, vote_count=vote_count, user_count=user_count, user_polls=user_polls)

@app.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = get_user(form.username.data)
        login_user(user)
        flash("You were logged in, %s." % user.displayname, "success")

        return redirect(request.args.get("next") or url_for("index"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    flash("You were logged out, %s. Goodbye!" % current_user.displayname, "success")
    logout_user()
    return redirect(request.args.get("next") or url_for("index"))

@app.route("/<slug>/", methods=("GET", "POST"))
def poll(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    comment_form = CommentForm()
    if poll.allow_comments and comment_form.validate_on_submit():
        comment = Comment()
        comment.created = datetime.utcnow()
        comment.text = comment_form.text.data.strip()

        if current_user.is_anonymous():
            comment.name = comment_form.name.data
        else:
            comment.user = current_user

        poll.comments.append(comment)
        flash("Your comment was saved.", "success")
        db.session.commit()
        return redirect(poll.get_url() + "#comment-" + str(comment.id))

    return render_template("poll.html", poll=poll, comment_form=comment_form)

@app.route("/<slug>/edit/", methods=("POST", "GET"))
def poll_edit(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    form = EditPollForm(obj=poll)

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

    poll.author = current_user
    db.session.commit()
    flash("You claimed this poll. Only you may edit it now.", "success")
    return redirect(url_for("poll_edit", slug=poll.slug))

@app.route("/<slug>/unclaim/", methods=("POST", "GET"))
@login_required
def poll_unclaim(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    if not poll.user_can_edit(current_user):
        abort(403)

    poll.author = None
    db.session.commit()
    flash("You freed this poll. Everyone may edit it now.", "success")
    return redirect(url_for("poll_edit", slug=poll.slug))


@app.route("/<slug>/choices/", methods=("POST", "GET"))
@app.route("/<slug>/choices/<int:step>", methods=("POST", "GET"))
def poll_edit_choices(slug, step=1):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    args = {}

    if poll.type == "date":
        form = DateTimeSelectForm()
        args["form"] = form

        if step == 1:
            form.dates.data = ",".join(set(choice.date.strftime("%Y-%m-%d") for choice in poll.choices))
            form.times.data = ",".join(set(choice.date.strftime("%H:%M") for choice in poll.choices))

        if step in (2, 3, 4) and form.validate_on_submit():
            dates = form.dates.data.split(",")
            times = form.times.data.split(",")
            args["dates"] = sorted(list(set(parser.parse(data, fuzzy=True).date() for data in dates)))
            args["times"] = sorted(list(set(parser.parse("1970-01-01 %s" % data, fuzzy=True).time() for data in times)))

        if step == 4 and form.validate_on_submit():
            # list all date/time combinations
            datetimes = [parser.parse(data) for data in request.form.getlist("datetimes[]")]

            if not datetimes:
                flash("Please select at least one combination.", "error")
            else:
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
                choice.deleted = False
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

        elif "edit" in request.args:
            eid = request.args.get("edit")
            choice = Choice.query.filter_by(id=eid, poll_id=poll.id).first_or_404()
            edit_form = EditChoiceForm(obj=choice)
            if edit_form.validate_on_submit():
                text = edit_form.text.data.strip()
                other_choice = Choice.query.filter_by(poll_id=poll.id, text=text).first()
                if other_choice and other_choice != choice:
                    flash("A choice with this text already exists.", "error")
                else:
                    choice.text = edit_form.text.data.strip()
                    db.session.commit()
                    flash("The choice was edited.", "success")
                    return redirect(url_for("poll_edit_choices", slug=poll.slug))
            args["edit_form"] = edit_form
            args["edit_id"] = choice.id

        args["form"] = form

    return render_template("poll_edit_choices.html", poll=poll, step=step, **args)

@app.route("/<slug>/values/", methods=("POST", "GET"))
def poll_edit_values(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    if "toggle" in request.args:
        value = ChoiceValue.query.filter_by(id=request.args["toggle"]).first_or_404()
        if value.poll != poll: abort(404)
        value.deleted = not value.deleted
        db.session.commit()
        flash("The choice value was %s." % ("removed" if value.deleted else "restored"), "success")
        return redirect(url_for("poll_edit_values", slug=poll.slug))

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

@app.route("/<slug>/vote", methods=("POST", "GET"))
def poll_vote(slug):
    poll = Poll.query.filter_by(slug=slug).first_or_404()

    if poll.require_login and current_user.is_anonymous():
        flash("You need to login to vote on this poll.", "error")
        return redirect(url_for("login", next=url_for("poll_vote", slug=poll.slug)))

    if poll.one_vote_per_user and not current_user.is_anonymous() and poll.get_user_votes(current_user):
        flash("You can only vote once on this poll. Please edit your choices by clicking the edit button on the right.", "error")
        return redirect(poll.get_url())

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
            if vote.anonymous and not vote.user:
                vote.name = "anonymous"

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

            flash("You have voted.", "success")
            db.session.commit()
            return redirect(poll.get_url())

    if not request.method == "POST":
        poll.fill_vote_form(form)

    return render_template("vote.html", poll=poll, form=form)

@app.route("/<slug>/vote/<int:vote_id>/edit", methods=("POST", "GET"))
def poll_vote_edit(slug, vote_id):
    poll = Poll.query.filter_by(slug=slug).first_or_404()
    vote = Vote.query.filter_by(id=vote_id).first_or_404()
    if vote.poll != poll: abort(404)

    if vote.user and current_user.is_anonymous():
        flash("This vote was created by a logged in user. If that was you, please log in to edit the vote.", "error")
        return redirect(url_for("login", next=url_for("poll_vote_edit", slug=poll.slug, vote_id=vote_id)))

    if vote.user and not current_user.is_anonymous() and vote.user != current_user:
        flash("This vote was created by someone else. You cannot edit their choices.", "error")
        return redirect(poll.get_url())

    form = CreateVoteForm(obj=vote)
    if poll.require_login and current_user.is_anonymous():
        flash("You need to login to edit votes on this poll.")
        return redirect(url_for("login", next=url_for("poll_vote_edit", slug=poll.slug, vote_id=vote_id)))

    if request.method == "POST":
        for subform in form.vote_choices:
            subform.value.choices = [(v.id, v.title) for v in poll.get_choice_values()]

        if form.validate_on_submit():
            if not vote.user:
                vote.name = form.name.data
            vote.anonymous = poll.anonymous_allowed and form.anonymous.data

            if vote.anonymous and not vote.user:
                vote.name = "anonymous"

            for subform in form.vote_choices:
                choice = Choice.query.filter_by(id=subform.choice_id.data).first()
                value = ChoiceValue.query.filter_by(id=subform.value.data).first()
                if not choice or choice.poll != poll: abort(404)
                if value and value.poll != poll: abort(404)

                vote_choice = poll.get_vote_choice(vote, choice)
                if not vote_choice:
                    vote_choice = VoteChoice()
                    vote_choice.vote = vote
                    vote_choice.choice = choice

                vote_choice.comment = subform.comment.data
                vote_choice.value = value

            db.session.commit()
            flash("The vote has been edited.", "success")
            return redirect(poll.get_url())

    if not request.method == "POST":
        poll.fill_vote_form(form)

    return render_template("vote.html", poll=poll, form=form, vote=vote)
