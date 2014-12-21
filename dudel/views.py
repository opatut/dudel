from dudel import app, db, babel, supported_languages
from dudel.models import Poll, User, Vote, VoteChoice, Choice, ChoiceValue, Comment, PollWatch, Member
from dudel.login import get_user
from dudel.forms import CreatePollForm, DateTimeSelectForm, AddChoiceForm, EditChoiceForm, AddValueForm, LoginForm, EditPollForm, CreateVoteChoiceForm, CreateVoteForm, CommentForm, LanguageForm, SettingsFormLdap, SettingsFormPassword
from dudel.util import PollExpiredException, PollActionException
import dudel.login
from flask import redirect, abort, request, render_template, flash, url_for, g
from flask.ext.babel import gettext
from flask.ext.login import current_user, login_required
from dateutil import parser
from datetime import datetime
import json

def get_poll(slug):
    return Poll.query.filter_by(slug=slug, deleted=False).first_or_404()

@babel.localeselector
def get_locale():
    if current_user.is_authenticated() and current_user.preferred_language:
        return current_user.preferred_language
    elif request.cookies.get("lang"):
        return request.cookies.get("lang")
    else:
        return request.accept_languages.best_match(supported_languages)


@app.route("/api/cron")
def cron():
    # This view should execute some regular tasks to be called by a cronjob, e.g.
    # by simply curl-ing "/api/cron"

    status = []

    # Update LDAP groups
    from dudel.plugins.ldapauth import ldap_connector
    ldap_connector.update_groups()
    status.append("updated LDAP groups")

    return "<br />".join(status)

@app.route("/api/members")
@login_required
def members():
    members = []

    for member in Member.query.all():
        members.append(dict(
            id=member.id,
            type=member.type,
            name=member.displayname))

    return json.dumps(members, indent=4)

@app.route("/", methods=("POST", "GET"))
def index():
    form = CreatePollForm()
    if form.validate_on_submit():
        poll = Poll()
        form.populate_obj(poll)
        db.session.add(poll)
        db.session.commit()
        flash(gettext("Poll created"))
        return redirect(url_for("poll_edit_choices", slug=poll.slug))

    polls = Poll.query.filter_by(deleted=False, public_listing=True).filter(not Poll.due_date or Poll.due_date >= datetime.utcnow()).order_by(db.desc(Poll.created)).all()

    poll_count = Poll.query.count()
    vote_count = Vote.query.count()
    user_count = User.query.count()

    return render_template("index.html", polls=polls, form=form, poll_count=poll_count, vote_count=vote_count, user_count=user_count)

@app.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()

    # The validator already performs the login via login.try_login
    if form.validate_on_submit():
        user = get_user(form.username.data)
        flash(gettext("You were logged in, %(name)s.", name=user.displayname), "success")

        return redirect(request.args.get("next") or url_for("index"))

    return render_template("login.html", form=form)

@app.route("/register", methods=("GET", "POST"))
def register():
    if not "password" in app.config["LOGIN_PROVIDERS"] or not app.config["REGISTRATIONS_ENABLED"]:
        abort(404)
    if current_user.is_authenticated():
        flash(gettext("You are already logged in."), "success")
        return redirect(request.args.get("next") or url_for("index"))
    form = RegisterForm()

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        dudel.login.force_login(user)
        flash(gettext("You were logged in, %(name)s.", name=user.displayname), "success")

        return redirect(request.args.get("next") or url_for("index"))

    return render_template("register.html", form=form)

@app.route("/logout")
def logout():
    if current_user.is_authenticated():
        flash(gettext("You were logged out, %(name)s. Goodbye!", name=current_user.displayname), "success")
        dudel.login.logout()
    return redirect(request.args.get("next") or url_for("index"))

@app.route("/user/language", methods=("GET", "POST"))
def user_change_language():
    response = redirect(request.args.get("next") or url_for("index"))

    form = LanguageForm()
    if form.validate_on_submit():
        lang = form.language.data
        if lang in supported_languages:
            if current_user.is_authenticated():
                current_user.preferred_language = lang
                db.session.commit()
            else:
                response.set_cookie("lang", lang)
    return response

@app.route("/user/settings", methods=("GET", "POST"))
@login_required
def user_settings():
    if current_user.source == "manual":
        form = SettingsFormPassword(obj=current_user)
    elif current_user.source == "ldap":
        form = SettingsFormLdap(obj=current_user)
    else:
        abort(404)

    if form.validate_on_submit():
        current_user.preferred_language = form.preferred_language.data
        current_user.autowatch = form.autowatch.data

        if current_user.source == "manual":
            form.populate_obj(current_user)
            if form.password1.data:
                current_user.set_password(form.password1.data)

        db.session.commit()
        flash(gettext("Your user settings were updated."), "success")
        return redirect(url_for('user_settings'))

    return render_template("user_settings.html", form=form)

@app.route("/<slug>/", methods=("GET", "POST"))
def poll(slug):
    poll = get_poll(slug)

    comment_form = CommentForm()
    if not "RECAPTCHA_PUBLIC_KEY" in app.config:
        del comment_form.captcha

    if poll.allow_comments and comment_form.validate_on_submit():
        comment = Comment()
        comment.created = datetime.utcnow()
        comment.text = comment_form.text.data.strip()

        if current_user.is_anonymous():
            comment.name = comment_form.name.data
        else:
            comment.user = current_user

        poll.comments.append(comment)
        flash(gettext("Your comment was saved."), "success")
        db.session.commit()
        return redirect(poll.get_url() + "#comment-" + str(comment.id))

    return render_template("poll.html", poll=poll, comment_form=comment_form)

@app.route("/<slug>/comment/delete/<int:id>", methods=("POST", "GET"))
def poll_delete_comment(slug, id):
    poll = get_poll(slug)
    comment = Comment.query.filter_by(id=id,poll=poll).first_or_404()
    if not comment.user_can_edit(current_user):
        abort(403)

    comment.deleted = True
    db.session.commit()
    flash(gettext("The comment was deleted."), "success")
    return redirect(poll.get_url())

@app.route("/<slug>/edit/", methods=("POST", "GET"))
def poll_edit(slug):
    poll = get_poll(slug)
    poll.check_edit_permission()
    form = EditPollForm(obj=poll)

    if current_user.is_authenticated():
        form.owner_id.choices = [(0, gettext("Nobody")),
            (current_user.id, current_user.displayname)]
        for group in current_user.groups:
            form.owner_id.choices.append((group.id, group.displayname))

        if poll.owner:
            current = (poll.owner.id, poll.owner.displayname)
            if not current in form.owner_id.choices:
                form.owner_id.choices.append(current)

    if form.validate_on_submit():
        form.populate_obj(poll)
        db.session.commit()
        flash(gettext("Poll settings have been saved."), "success")
        #return redirect(poll.get_url())
        return redirect(url_for("poll_edit", slug=poll.slug))
    else:
        form.owner_id.data = poll.owner_id


    return render_template("poll_edit.html", poll=poll, form=form)


@app.route("/<slug>/watch/<watch>", methods=("POST", "GET"))
@login_required
def poll_watch(slug, watch):
    poll = get_poll(slug)

    if not watch in ("yes", "no"): abort(404)
    watch = (watch == "yes")

    PollWatch.query.filter_by(poll=poll, user=current_user).delete()
    if watch:
        db.session.add(PollWatch(poll, current_user))
    db.session.commit()

    flash(gettext("You are now watching this poll.") if watch else gettext("You are not watching this poll anymore."), "success")
    return redirect(request.args.get("next", None) or poll.get_url())

@app.route("/<slug>/choices/", methods=("POST", "GET"))
@app.route("/<slug>/choices/<int:step>", methods=("POST", "GET"))
def poll_edit_choices(slug, step=1):
    poll = get_poll(slug)
    poll.check_expiry()
    poll.check_edit_permission()
    args = {}

    if poll.type == "date":
        form = DateTimeSelectForm()
        args["form"] = form

        if step == 1:
            form.dates.data = ",".join(set(choice.date.strftime("%Y-%m-%d") for choice in poll.choices if not choice.deleted))
            form.times.data = ",".join(set(choice.date.strftime("%H:%M") for choice in poll.choices if not choice.deleted))

        if step in (2, 3, 4) and form.validate_on_submit():
            dates = form.dates.data.split(",")
            times = form.times.data.split(",")
            args["dates"] = sorted(list(set(parser.parse(data, fuzzy=True).date() for data in dates)))
            args["times"] = sorted(list(set(parser.parse("1970-01-01 %s" % data, fuzzy=True).time() for data in times)))

        if step == 4 and form.validate_on_submit():
            # list all date/time combinations
            datetimes = [parser.parse(data) for data in request.form.getlist("datetimes[]")]

            if not datetimes:
                flash(gettext("Please select at least one combination."), "error")
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
                flash(gettext("The choices list has been updated."), "success")
                return redirect(poll.get_url())
    elif poll.type == "day":
        form = DateTimeSelectForm()
        args["form"] = form

        if form.validate_on_submit():
            dates = form.dates.data.split(",")
            dates = sorted(list(set(parser.parse(data, fuzzy=True).date() for data in dates)))

            if not dates:
                flash(gettext("Please select at least one date."), "error")
            else:
                existing_dates = [choice.date.date() for choice in poll.choices]

                # disable all that are not listed
                for choice in poll.choices:
                    choice.deleted = not choice.date.date() in dates

                # create those that don't exist yet
                for date in dates:
                    if not date in existing_dates:
                        choice = Choice()
                        choice.date = date
                        poll.choices.append(choice)
                        db.session.add(choice)

                db.session.commit()
                flash(gettext("The choices list has been updated."), "success")
                return redirect(poll.get_url())
        else:
            form.dates.data = ",".join(set(choice.date.strftime("%Y-%m-%d") for choice in poll.choices if not choice.deleted))


    else:
        form = AddChoiceForm()

        if form.validate_on_submit():
            text = form.text.data.strip()
            choice = Choice.query.filter_by(poll_id=poll.id, text=text).first()
            if choice:
                choice.deleted = False
                if not poll.choice_groups_valid(choice.get_hierarchy(), choice.id):
                    flash(gettext("This choice text is not allowed due to grouping conflicts."), "error")
                    return redirect(url_for("poll_edit_choices", slug=poll.slug))

            else:
                choice = Choice()
                choice.text = form.text.data

                if not poll.choice_groups_valid(choice.get_hierarchy()):
                    flash(gettext("This choice text is not allowed due to grouping conflicts."), "error")
                    return redirect(url_for("poll_edit_choices", slug=poll.slug))

                poll.choices.append(choice)
                db.session.add(choice)

            db.session.commit()

            if choice.deleted:
                flash(gettext("The choice was disabled."), "success")
            else:
                flash(gettext("The choice was added."), "success")
            return redirect(url_for("poll_edit_choices", slug=poll.slug))

        if "toggle" in request.args:
            tid = request.args.get("toggle")
            choice = Choice.query.filter_by(id=tid, poll_id=poll.id).first_or_404()
            choice.deleted = not choice.deleted

            if not choice.deleted and not poll.choice_groups_valid(choice.get_hierarchy(), choice.id):
                flash(gettext("You cannot undelete this choice due to grouping conflicts."), "error")
                return redirect(url_for("poll_edit_choices", slug=poll.slug))

            db.session.commit()
            if choice.deleted:
                flash(gettext("The choice was disabled."), "success")
            else:
                flash(gettext("The choice was added."), "success")
            return redirect(url_for("poll_edit_choices", slug=poll.slug))

        elif "edit" in request.args:
            eid = request.args.get("edit")
            choice = Choice.query.filter_by(id=eid, poll_id=poll.id).first_or_404()
            edit_form = EditChoiceForm(obj=choice)
            if edit_form.validate_on_submit():
                text = edit_form.text.data.strip()
                other_choice = Choice.query.filter_by(poll_id=poll.id, text=text).first()
                if other_choice and other_choice != choice:
                    flash(gettext("A choice with this text already exists."), "error")
                else:
                    choice.text = edit_form.text.data.strip()

                    if not poll.choice_groups_valid(choice.get_hierarchy(), choice.id):
                        flash(gettext("This choice text is not allowed due to grouping conflicts."), "error")
                    else:
                        db.session.commit()
                        flash(gettext("The choice was edited."), "success")
                        return redirect(url_for("poll_edit_choices", slug=poll.slug))
            args["edit_form"] = edit_form
            args["edit_id"] = choice.id

        args["form"] = form

    return render_template("poll_edit_choices.html", poll=poll, step=step, **args)

@app.route("/<slug>/values/", methods=("POST", "GET"))
def poll_edit_values(slug):
    poll = get_poll(slug)
    poll.check_expiry()
    poll.check_edit_permission()

    args = {}

    if "toggle" in request.args:
        value = ChoiceValue.query.filter_by(id=request.args["toggle"]).first_or_404()
        if value.poll != poll: abort(404)
        value.deleted = not value.deleted
        db.session.commit()
        if value.deleted:
            flash(gettext("The choice value was removed."), "success")
        else:
            flash(gettext("The choice value restored."), "success")

        return redirect(url_for("poll_edit_values", slug=poll.slug))

    elif "edit" in request.args:
        id = request.args.get("edit")
        value = ChoiceValue.query.filter_by(poll_id=poll.id, id=id).first_or_404()
        form = AddValueForm(obj=value)
        if form.validate_on_submit():
            value.title = form.title.data
            value.icon = form.icon.data
            value.color = form.color.data.lstrip("#")
            value.weight = form.weight.data
            db.session.commit()
            flash(gettext("The choice value was edited."), "success")
            return redirect(url_for("poll_edit_values", slug=poll.slug))
        args["form"] = form
        args["edit_value"] = value

    else:
        form = AddValueForm()
        if form.validate_on_submit():
            value = ChoiceValue()
            value.title = form.title.data
            value.icon = form.icon.data
            value.color = form.color.data.lstrip("#")
            value.weight = form.weight.data
            value.poll = poll
            db.session.add(value)
            db.session.commit()
            flash(gettext("The choice value was added."), "success")
            return redirect(url_for("poll_edit_values", slug=poll.slug))
        args["form"] = form

    return render_template("poll_edit_values.html", poll=poll, **args)

@app.route("/<slug>/delete", methods=("POST", "GET"))
def poll_delete(slug):
    poll = get_poll(slug)

    if "confirm" in request.args:
        poll.deleted = True
        db.session.commit()
        flash(gettext("The poll was deleted."), "success")
        return redirect(url_for("index"))

    return render_template("poll_delete.html", poll=poll)

@app.route("/<slug>/vote", methods=("POST", "GET"))
def poll_vote(slug):
    poll = get_poll(slug)
    poll.check_expiry()

    if poll.require_login and current_user.is_anonymous():
        flash(gettext("You need to login to vote on this poll."), "error")
        return redirect(url_for("login", next=url_for("poll_vote", slug=poll.slug)))

    if poll.one_vote_per_user and not current_user.is_anonymous() and poll.get_user_votes(current_user):
        flash(gettext("You can only vote once on this poll. Please edit your choices by clicking the edit button on the right."), "error")
        return redirect(poll.get_url())


    groups = poll.get_choice_groups()
    if not groups:
        flash(gettext("The poll owner has not yet created any choices. You cannot vote on the poll yet."), "warning")
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

            vote.comment = form.comment.data

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

            flash(gettext("You have voted."), "success")

            poll.send_watchers("[Dudel] New vote: " + poll.title,
                "email/poll_voted.txt", voter=vote.displayname)

            db.session.commit()

            if current_user.is_authenticated() and current_user.autowatch:
                return redirect(url_for("poll_watch", slug=poll.slug, watch="yes", next=poll.get_url()))
            else:
                return redirect(poll.get_url())

    if not request.method == "POST":
        poll.fill_vote_form(form)

    return render_template("vote.html", poll=poll, form=form)

@app.route("/<slug>/vote/<int:vote_id>/edit", methods=("POST", "GET"))
def poll_vote_edit(slug, vote_id):
    poll = get_poll(slug)
    poll.check_expiry()

    vote = Vote.query.filter_by(id=vote_id).first_or_404()
    if vote.poll != poll: abort(404)

    if vote.user and current_user.is_anonymous():
        flash(gettext("This vote was created by a logged in user. If that was you, please log in to edit the vote."), "error")
        return redirect(url_for("login", next=url_for("poll_vote_edit", slug=poll.slug, vote_id=vote_id)))

    if vote.user and not current_user.is_anonymous() and vote.user != current_user:
        flash(gettext("This vote was created by someone else. You cannot edit their choices."), "error")
        return redirect(poll.get_url())

    form = CreateVoteForm(obj=vote)
    if poll.require_login and current_user.is_anonymous():
        flash(gettext("You need to login to edit votes on this poll."))
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

            vote.comment = form.comment.data

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
            flash(gettext("The vote has been edited."), "success")
            return redirect(poll.get_url())

    if not request.method == "POST":
        poll.fill_vote_form(form)
        for subform in form.vote_choices:
            vote_choice = VoteChoice.query.filter_by(vote_id = vote.id, choice_id = subform.choice_id.data).first()
            subform.comment.data = vote_choice.comment if vote_choice else ""

    return render_template("vote.html", poll=poll, form=form, vote=vote)

@app.route("/<slug>/vote/<int:vote_id>/delete", methods=("POST", "GET"))
def poll_vote_delete(slug, vote_id):
    poll = get_poll(slug)
    poll.check_expiry()

    vote = Vote.query.filter_by(id=vote_id).first_or_404()
    if vote.poll != poll: abort(404)

    if not vote.user_can_delete(current_user): abort(403)

    db.session.delete(vote)
    db.session.commit()
    flash(gettext("The vote has been deleted"), "success")
    return redirect(poll.get_url())


@app.errorhandler(PollExpiredException)
def poll_expired(e):
    flash(gettext("This poll is expired. You cannot vote or edit your choice anymore."), "error")
    return redirect(e.poll.get_url())

@app.errorhandler(PollActionException)
def poll_action(e):
    if current_user.is_anonymous():
        flash(gettext("You do not have permission to %(action)s this poll. Please log in and try again.", action=e.action), "error")
        return redirect(url_for("login", next=request.url))
    else:
        flash(gettext("You do not have permission to %(action)s this poll.", action=e.action), "error")
        return redirect(e.poll.get_url())

@app.route('/static/translations/<locale>.po')
def root(locale):
    if locale not in ("de",):
        abort(404)
    return open('dudel/translations/%s/LC_MESSAGES/messages.po' % locale).read()
