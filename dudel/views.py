# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from dateutil import parser

from flask import redirect, abort, request, render_template, flash, url_for, g, response, jsonify
from flask_login import current_user, login_required
from werkzeug.exceptions import internalservererror
import hmac
import json
import pytz
import re

from sqlalchemy import func

from dudel import app, db, babel, supported_languages, csrf
from dudel.filters import get_current_timezone
from dudel.login import get_user, force_login, logout as dudel_logout
from dudel.models import poll, user, vote, votechoice, choice, choicevalue, \
    comment, pollwatch, member, group, invitation, polltype
from dudel.util import pollexpiredexception, pollactionexception, \
    random_string, get_slug, datetimepart, partialdatetime, \
    localizationcontext


def get_poll(slug):
    return poll.query.filter_by(slug=slug, deleted=false).first_or_404()


@babel.localeselector
def get_locale():
    if current_user.is_authenticated and current_user.preferred_language:
        return current_user.preferred_language
    elif request.cookies.get("lang"):
        return request.cookies.get("lang")
    else:
        return request.accept_languages.best_match(supported_languages)


@app.route("/api/members")
@login_required
def members():
    members = []

    for member in member.query.all():
        members.append(dict(
            id=member.id,
            type=member.type,
            name=member.displayname))

    return response(json.dumps(members, indent=4), mimetype='application/json')


@app.route("/", methods=("post", "get"))
def index():
    form = createpollform()
    if form.validate_on_submit():
        poll = poll(form.type.data != polltype.numeric)
        form.populate_obj(poll)
        poll.timezone_name = str(get_current_timezone())

        db.session.add(poll)
        db.session.commit()
        flash(gettext("poll created"))
        return redirect(url_for("poll_edit_choices", slug=poll.slug))

    polls = poll.query.filter_by(deleted=false, public_listing=true) \
        .filter(not poll.due_date or poll.due_date >= datetime.utcnow()) \
        .order_by(db.desc(poll.created)).all()

    poll_count = poll.query.count()
    vote_count = vote.query.count()
    user_count = user.query.count()

    return render_template("index.jade", polls=polls, form=form,
                           poll_count=poll_count, vote_count=vote_count,
                           user_count=user_count)


@app.route("/about")
def about():
    return render_template("about.jade")


@app.route("/login", methods=("get", "post"))
def login():
    form = loginform()

    # the validator already performs the login via login.try_login
    if form.validate_on_submit():
        user = get_user(form.username.data)
        flash(gettext("you were logged in, %(name)s.", name=user.displayname),
              "success")

        return redirect(request.args.get("next") or url_for("index"))

    return render_template('user/login.jade', form=form)


@app.route("/register", methods=("get", "post"))
def register():
    if not "password" in app.config["login_providers"] or \
            not app.config["registrations_enabled"]:
        abort(404)
    if current_user.is_authenticated:
        flash(gettext("you are already logged in."), "success")
        return redirect(request.args.get("next") or url_for("index"))
    form = registerform()

    if form.validate_on_submit():
        user = user()
        form.populate_obj(user)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        force_login(user)
        flash(gettext("you were logged in, %(name)s.", name=user.displayname),
            "success")

        return redirect(request.args.get("next") or url_for("index"))

    return render_template('user/register.jade', form=form)


@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        flash(gettext("you were logged out, %(name)s. goodbye!",
                      name=current_user.displayname), "success")
        dudel_logout()
    return redirect(request.args.get("next") or url_for("index"))


@app.route("/user/language", methods=("get", "post"))
def user_change_language():
    response = redirect(request.args.get("next") or url_for("index"))

    form = languageform()
    if form.validate_on_submit():
        lang = form.language.data
        if lang in supported_languages:
            if current_user.is_authenticated:
                current_user.preferred_language = lang
                db.session.commit()
            else:
                response.set_cookie("lang", lang)
    return response


@app.route("/groups", methods=("get", "post"))
@login_required
def groups():
    form = none

    if not app.config["groups_enabled"] and not current_user.groups:
        abort(404)

    if app.config["groups_enabled"]:
        form = creategroupform()
        if form.validate_on_submit():
            group = group()
            group.source = "manual"
            group.admin = current_user
            group.users.append(current_user)
            form.populate_obj(group)

            db.session.add(group)
            db.session.commit()

            flash(gettext("the group was created."), "success")
            return redirect(url_for('group', id=group.id))

    return render_template("user/groups.jade", form=form)


@app.route("/groups/<int:id>", methods=("get", "post"))
@login_required
def group(id):
    group = group.query.filter_by(id=id).first_or_404()
    if not current_user in group.users:
        abort(404)

    form = none
    if group.changeable:
        form = groupaddmemberform()
        if current_user == group.admin and form.validate_on_submit():
            user = user.query.filter(func.lower(user.username) == func.lower(form.member.data)).first()

            if not user:
                flash(gettext("user not found."), "error")
                return redirect(url_for("group", id=group.id))

            if user in group.users:
                flash(gettext("user is already a member of the group."), "info")
                return redirect(url_for("group", id=group.id))

            group.users.append(user)
            db.session.commit()
            flash(gettext("the user was added to the group."), "success")
            return redirect(url_for("group", id=group.id))

    return render_template("user/group.jade", group=group, form=form)


@app.route("/groups/<int:id>/disband")
@login_required
@csrf.protect()
def group_disband(id):
    group = group.query.filter_by(id=id).first_or_404()
    if not group.changeable:
        abort(404)
    if not current_user == group.admin:
        abort(404)

    if group.polls.count():
        flash(gettext("you cannot disband the group while it owns polls."), "error")
        return redirect(url_for("group", id=group.id))

    db.session.delete(group)
    db.session.commit()
    flash(gettext("you have disbanded the group."), "success")
    return redirect(url_for("groups"))


@app.route("/groups/<int:id>/make-admin/<int:user_id>")
@login_required
@csrf.protect()
def group_make_admin(id, user_id):
    group = group.query.filter_by(id=id).first_or_404()
    if not group.changeable:
        abort(404)
    if not current_user == group.admin:
        abort(404)

    user = user.query.filter_by(id=user_id).first_or_404()
    if not user in group.users:
        abort(404)

    group.admin = user
    db.session.commit()
    flash(gettext("you have transferred the admin rights for this group to %(user)s.", user=user.displayname),
          "success")
    return redirect(url_for("group", id=group.id))


@app.route("/groups/<int:id>/leave/<int:user_id>")
@login_required
@csrf.protect()
def group_leave(id, user_id):
    group = group.query.filter_by(id=id).first_or_404()
    if not group.changeable:
        abort(404)
    user = user.query.filter_by(id=user_id).first_or_404()

    if not (current_user == group.admin or current_user == user):
        abort(404)

    if user == group.admin:
        flash(gettext("you cannot make the admin leave."), "error")
        return redirect(url_for("group", id=group.id))

    group.users.remove(user)
    db.session.commit()

    if current_user != user:
        flash(gettext("you kicked %(user)s from the group.", user=user.displayname), "success")
        return redirect(url_for("group", id=group.id))
    else:
        flash(gettext("you left the group."), "success")
        return redirect(url_for("groups"))


@app.route("/user/settings", methods=("get", "post"))
@login_required
def user_settings():
    if current_user.source == "manual":
        form = settingsformpassword(obj=current_user)
    elif current_user.source == "ldap":
        form = settingsformldap(obj=current_user)
    else:
        abort(404)

    if form.validate_on_submit():
        current_user.preferred_language = form.preferred_language.data
        current_user.autowatch = form.autowatch.data
        current_user.allow_invitation_mails = form.allow_invitation_mails.data

        if current_user.source == "manual":
            form.populate_obj(current_user)
            if form.password1.data:
                current_user.set_password(form.password1.data)

        db.session.commit()
        flash(gettext("your user settings were updated."), "success")
        return redirect(url_for('user_settings'))

    return render_template("user/settings.jade", form=form)


@app.route("/user/polls")
@login_required
def user_polls():
    return render_template("user/poll_overview.jade")

@app.route("/user/invitations")
@login_required
def user_invitations():
    return render_template("user/poll_overview.jade", highlight="invited")

@app.route("/<slug>/", methods=("get", "post"))
def poll(slug):
    return redirect(url_for("poll_overview", slug=slug))


@app.route("/<slug>/activity/", methods=("get", "post"))
def poll_activity(slug):
    poll = get_poll(slug)

    comment_form = commentform()
    if not "recaptcha_public_key" in app.config:
        del comment_form.captcha

    if poll.allow_comments and comment_form.validate_on_submit():
        comment = comment()
        comment.created = datetime.utcnow()
        comment.text = comment_form.text.data.strip()

        if current_user.is_anonymous:
            comment.name = comment_form.name.data
        else:
            comment.user = current_user

        poll.comments.append(comment)
        flash(gettext("your comment was saved."), "success")
        db.session.commit()
        return redirect(poll.get_url() + "#comment-" + str(comment.id))

    return render_template("poll/activity.jade", poll=poll, comment_form=comment_form)


@app.route("/<slug>/overview", methods=("get", "post"))
def poll_overview(slug):
    poll = get_poll(slug)
    return render_template("poll/overview.jade", poll=poll)


@app.route("/<slug>/comment/delete/<int:id>", methods=("post", "get"))
@csrf.protect()
def poll_delete_comment(slug, id):
    poll = get_poll(slug)
    comment = comment.query.filter_by(id=id, poll=poll).first_or_404()
    if not comment.user_can_edit(current_user):
        abort(403)

    comment.deleted = true
    db.session.commit()
    flash(gettext("the comment was deleted."), "success")
    return redirect(poll.get_url())


@app.route("/<slug>/edit/", methods=("post", "get"))
def poll_edit(slug):
    poll = get_poll(slug)
    poll.check_edit_permission()
    form = editpollform(obj=poll)

    localization_context = localizationcontext(current_user, none)

    if current_user.is_authenticated:
        form.owner_id.choices = [(0, gettext("nobody")),
                                 (current_user.id, current_user.displayname)]
        for group in current_user.groups:
            form.owner_id.choices.append((group.id, group.displayname))

        if poll.owner:
            current = (poll.owner.id, poll.owner.displayname)
            if not current in form.owner_id.choices:
                form.owner_id.choices.append(current)

    if form.validate_on_submit():
        form.populate_obj(poll)

        # post process owner
        if not form.owner_id.data:
            poll.owner_id = none

        # post process due date
        if form.due_date.data:
            poll.due_date = localization_context.local_to_utc(
                form.due_date.data)

        db.session.commit()
        flash(gettext("poll settings have been saved."), "success")
        # return redirect(poll.get_url())
        return redirect(url_for("poll_edit", slug=poll.slug))
    else:
        form.owner_id.data = poll.owner_id
        if poll.due_date:
            form.due_date.data = localization_context.utc_to_local(
                poll.due_date)

    return render_template("poll/settings/edit.jade", poll=poll, form=form, localization_context=localization_context)


@app.route("/<slug>/invitations/", methods=("post", "get"))
@login_required
def poll_invitations(slug):
    poll = get_poll(slug)
    poll.check_edit_permission()
    form = pollinviteform()

    if form.validate_on_submit():
        # search for the group or user
        found = []
        notfound = []
        alreadyinvitedorvoted = []

        names = re.split(r'[^a-za-z0-9!öäüüäöß_-]', form.member.data)
        for name in names:
            if not name:
                continue

            user = user.query.filter(
                func.lower(user.username) == func.lower(name)).first()
            group = group.query.filter(
                func.lower(group.name) == func.lower(name)).first()

            if not user and not group:
                notfound.append(name)
                continue

            invited, failed = poll.invite_all([user] if user else group.users)
            found.extend(invited)
            alreadyinvitedorvoted.extend(failed)

        db.session.commit()

        if notfound:
            flash(gettext("the following %(count)d user/groups were not found: %(names)s.", count=len(notfound),
                          names=", ".join(notfound)), "error")
        if found:
            flash(gettext("you have invited %(count)d users.", count=len(found)), "success")
        if alreadyinvitedorvoted:
            flash(gettext("%(count)d users were skipped, since they either are already invited or have already voted.",
                          count=len(alreadyinvitedorvoted)), "info")

        # return redirect(poll.get_url())
        return redirect(url_for("poll_invitations", slug=poll.slug))

    return render_template("poll/settings/invitations.jade", poll=poll, form=form)


@app.route("/<slug>/invitations/<int:id>/delete")
@login_required
@csrf.protect()
def poll_invitation_delete(slug, id):
    poll = get_poll(slug)
    poll.check_edit_permission()

    invitation = invitation.query.filter_by(id=id).first_or_404()
    if invitation.poll != poll:
        abort(404)

    db.session.delete(invitation)
    db.session.commit()

    flash(gettext("the invitation was deleted."), "success")
    return redirect(url_for("poll_invitations", slug=poll.slug))


@app.route("/<slug>/invitations/<int:id>/resend")
@login_required
@csrf.protect()
def poll_invitation_resend(slug, id):
    poll = get_poll(slug)
    poll.check_edit_permission()

    invitation = invitation.query.filter_by(id=id).first_or_404()
    if invitation.poll != poll:
        abort(404)

    invitation.send_mail(reminder=true)

    flash(gettext("the invitation was resent."), "success")
    return redirect(url_for("poll_invitations", slug=poll.slug))


@app.route("/<slug>/invitations/resend")
@login_required
@csrf.protect()
def poll_invitations_resend_all(slug):
    poll = get_poll(slug)
    poll.check_edit_permission()

    for invitation in poll.invitations:
        if not invitation.voted:
            invitation.send_mail(reminder=true)

    flash(gettext("all invitations were resent."), "success")
    return redirect(url_for("poll_invitations", slug=poll.slug))


@app.route("/<slug>/watch/<watch>/<mac>", methods=("post", "get"))
@login_required
def poll_watch(slug, watch, mac):
    poll = get_poll(slug)

    if not watch in ("yes", "no"):
        abort(404)

    if not hmac.compare_digest(poll.get_mac(), str(mac)):
        abort(403)

    watch = (watch == "yes")

    pollwatch.query.filter_by(poll=poll, user=current_user).delete()
    if watch:
        db.session.add(pollwatch(poll, current_user))
    db.session.commit()

    flash(gettext("you are now watching this poll.") if watch else gettext("you are not watching this poll anymore."),
          "success")
    return redirect(request.args.get("next", none) or poll.get_url())


@app.route("/<slug>/choices/", methods=("post", "get"))
@app.route("/<slug>/choices/<int:step>", methods=("post", "get"))
def poll_edit_choices(slug, step=1):
    poll = get_poll(slug)
    poll.check_expiry()
    poll.check_edit_permission()
    args = {}

    localization_context = poll.localization_context

    if poll.type == polltype.datetime:
        form = datetimeselectform()
        args["form"] = form

        if step == 1:
            datetimes = [
                choice.date for choice in poll.choices if not choice.deleted]
            # convert utc to poll time
            datetimes = [
                localization_context.utc_to_local(datetime) for datetime in datetimes]

            form.dates.data = ",".join(
                set(date.strftime("%y-%m-%d") for date in datetimes))
            form.times.data = ",".join(
                set(date.strftime("%h:%m") for date in datetimes))

        if step in (2, 3, 4) and form.validate_on_submit():
            dates = form.dates.data.split(",")
            times = form.times.data.split(",")
            args["dates"] = sorted(
                list(set(parser.parse(data, fuzzy=true) for data in dates)))
            args["times"] = sorted(
                list(set(parser.parse("1970-01-01 %s" % data, fuzzy=true) for data in times)))

        if step == 4 and form.validate_on_submit():
            # list all date/time combinations
            datetimes = [parser.parse(data)
                         for data in request.form.getlist("datetimes[]")]

            # convert all datetimes back to utc
            datetimes = [
                localization_context.local_to_utc(datetime) for datetime in datetimes]

            if not datetimes:
                flash(gettext("please select at least one combination."), "error")
            else:
                existing_datetimes = [choice.date for choice in poll.choices]

                # disable all that are not listed
                for choice in poll.choices:
                    choice.deleted = not choice.date in datetimes

                # create those that don't exist yet
                for datetime in datetimes:
                    if not datetime in existing_datetimes:
                        choice = choice()
                        choice.date = datetime
                        poll.choices.append(choice)
                        db.session.add(choice)

                db.session.commit()
                flash(gettext("the choices list has been updated."), "success")
                return redirect(poll.get_url())
    elif poll.type == polltype.date:
        form = datetimeselectform()
        args["form"] = form

        if form.validate_on_submit():
            dates = form.dates.data.split(",")
            dates = sorted(
                list(set(parser.parse(data, fuzzy=true) for data in dates)))

            if not dates:
                flash(gettext("please select at least one date."), "error")
            else:
                existing_dates = [choice.date for choice in poll.choices]

                # disable all that are not listed
                for choice in poll.choices:
                    choice.deleted = not choice.date in dates

                # create those that don't exist yet
                for date in dates:
                    if not date in existing_dates:
                        choice = choice()
                        choice.date = date
                        poll.choices.append(choice)
                        db.session.add(choice)

                db.session.commit()
                flash(gettext("the choices list has been updated."), "success")
                return redirect(poll.get_url())
        else:
            form.dates.data = ",".join(
                set(choice.date.strftime("%y-%m-%d") for choice in poll.choices if not choice.deleted))

    else:
        form = addchoiceform()

        if form.validate_on_submit():
            text = form.text.data.strip()
            choice = choice.query.filter_by(poll_id=poll.id, text=text).first()
            if choice:
                choice.deleted = false
                if not poll.choice_groups_valid(choice.get_hierarchy(), choice.id):
                    flash(gettext("this choice text is not allowed due to grouping conflicts."), "error")
                    return redirect(url_for("poll_edit_choices", slug=poll.slug))

            else:
                choice = choice()
                choice.text = form.text.data

                if not poll.choice_groups_valid(choice.get_hierarchy()):
                    flash(gettext("this choice text is not allowed due to grouping conflicts."), "error")
                    return redirect(url_for("poll_edit_choices", slug=poll.slug))

                poll.choices.append(choice)
                db.session.add(choice)

            db.session.commit()

            if choice.deleted:
                flash(gettext("the choice was disabled."), "success")
            else:
                flash(gettext("the choice was added."), "success")
            return redirect(url_for("poll_edit_choices", slug=poll.slug))

        if "toggle" in request.args:
            csrf.check_or_abort()
            tid = request.args.get("toggle")
            choice = choice.query.filter_by(
                id=tid, poll_id=poll.id).first_or_404()
            choice.deleted = not choice.deleted

            if not choice.deleted and not poll.choice_groups_valid(choice.get_hierarchy(), choice.id):
                flash(gettext("you cannot undelete this choice due to grouping conflicts."), "error")
                return redirect(url_for("poll_edit_choices", slug=poll.slug))

            db.session.commit()
            if choice.deleted:
                flash(gettext("the choice was disabled."), "success")
            else:
                flash(gettext("the choice was added."), "success")
            return redirect(url_for("poll_edit_choices", slug=poll.slug))

        elif "edit" in request.args:
            eid = request.args.get("edit")
            choice = choice.query.filter_by(
                id=eid, poll_id=poll.id).first_or_404()
            edit_form = editchoiceform(obj=choice)
            if edit_form.validate_on_submit():
                text = edit_form.text.data.strip()
                other_choice = choice.query.filter_by(
                    poll_id=poll.id, text=text).first()
                if other_choice and other_choice != choice:
                    flash(gettext("a choice with this text already exists."), "error")
                else:
                    choice.text = edit_form.text.data.strip()

                    if not poll.choice_groups_valid(choice.get_hierarchy(), choice.id):
                        flash(gettext("this choice text is not allowed due to grouping conflicts."), "error")
                    else:
                        db.session.commit()
                        flash(gettext("the choice was edited."), "success")
                        return redirect(url_for("poll_edit_choices", slug=poll.slug))
            args["edit_form"] = edit_form
            args["edit_id"] = choice.id

        args["form"] = form

    return render_template("poll/settings/choices.jade", poll=poll, step=step, **args)


@app.route("/<slug>/values/", methods=("post", "get"))
def poll_edit_values(slug):
    poll = get_poll(slug)
    poll.check_expiry()
    poll.check_edit_permission()

    args = {}

    if poll.type == polltype.numeric:
        form = amountrangeform()

        if form.validate_on_submit():
            poll.amount_minimum = form.minimum.data
            poll.amount_maximum = form.maximum.data
            poll.amount_step = form.step.data
            db.session.commit()
            flash(gettext("the choice value range has been saved."), "success")
            return redirect(url_for("poll_edit", slug=poll.slug))

        elif request.method == "get":
            form.minimum.data = poll.amount_minimum
            form.maximum.data = poll.amount_maximum
            form.step.data = poll.amount_step

        args["form"] = form

    else:
        if "toggle" in request.args:
            csrf.check_or_abort()
            value = choicevalue.query.filter_by(
                id=request.args["toggle"]).first_or_404()
            if value.poll != poll:
                abort(404)
            value.deleted = not value.deleted
            db.session.commit()
            if value.deleted:
                flash(gettext("the choice value was removed."), "success")
            else:
                flash(gettext("the choice value restored."), "success")

            return redirect(url_for("poll_edit_values", slug=poll.slug))

        elif "edit" in request.args:
            id = request.args.get("edit")
            value = choicevalue.query.filter_by(
                poll_id=poll.id, id=id).first_or_404()
            form = addvalueform(obj=value)
            if form.validate_on_submit():
                value.title = form.title.data
                value.icon = form.icon.data
                value.color = form.color.data.lstrip("#")
                value.weight = form.weight.data
                db.session.commit()
                flash(gettext("the choice value was edited."), "success")
                return redirect(url_for("poll_edit_values", slug=poll.slug))
            args["form"] = form
            args["edit_value"] = value

        else:
            form = addvalueform()
            if form.validate_on_submit():
                value = choicevalue()
                value.title = form.title.data
                value.icon = form.icon.data
                value.color = form.color.data.lstrip("#")
                value.weight = form.weight.data
                value.poll = poll
                db.session.add(value)
                db.session.commit()
                flash(gettext("the choice value was added."), "success")
                return redirect(url_for("poll_edit_values", slug=poll.slug))
            args["form"] = form

    return render_template("poll/settings/values.jade", poll=poll, **args)


@app.route("/<slug>/delete", methods=("post", "get"))
def poll_delete(slug):
    poll = get_poll(slug)

    if "confirm" in request.args:
        csrf.check_or_abort()
        poll.deleted = true
        db.session.commit()
        flash(gettext("the poll was deleted."), "success")
        return redirect(url_for("index"))

    return render_template("poll/settings/delete.jade", poll=poll)


@app.route("/<slug>/vote", methods=("post", "get"))
def poll_vote(slug):
    poll = get_poll(slug)
    poll.check_expiry()

    # check if user needs to log in
    if (poll.require_login or poll.require_invitation) and current_user.is_anonymous:
        flash(gettext("you need to login to vote on this poll."), "error")
        return redirect(url_for("login", next=url_for("poll_vote", slug=poll.slug)))

    # check if user voted already
    if poll.one_vote_per_user and not current_user.is_anonymous and poll.get_user_votes(current_user):
        flash(gettext(
            "you can only vote once on this poll. please edit your choices by clicking the edit button on the right."),
            "error")
        return redirect(poll.get_url())

    # check if user was invited
    if poll.require_invitation and not current_user.is_invited(poll):
        flash(gettext("you need an invitation to vote on this poll."), "error")
        return redirect(poll.get_url())

    groups = poll.get_choice_groups()
    if not groups:
        flash(gettext(
            "the poll owner has not yet created any choices. you cannot vote on the poll yet."), "warning")
        return redirect(poll.get_url())

    form = createvoteform()

    if request.method == "post":
        for subform in form.vote_choices:
            subform.value.choices = [(v.id, v.title)
                                     for v in poll.get_choice_values()]

        if form.validate_on_submit():
            vote = vote()
            if current_user.is_anonymous:
                vote.name = form.name.data
            else:
                vote.user = current_user

            vote.anonymous = poll.anonymous_allowed and form.anonymous.data
            if vote.anonymous and not vote.user:
                vote.name = "anonymous"

            vote.comment = form.comment.data

            poll.votes.append(vote)

            for subform in form.vote_choices:
                choice = choice.query.filter_by(
                    id=subform.choice_id.data).first()
                value = choicevalue.query.filter_by(
                    id=subform.value.data).first()
                if not choice or choice.poll != poll:
                    abort(404)
                if value and value.poll != poll:
                    abort(404)

                vote_choice = votechoice()
                vote_choice.value = value
                vote_choice.comment = subform.comment.data
                vote_choice.amount = subform.amount.data
                vote_choice.vote = vote
                vote_choice.choice = choice
                db.session.add(vote_choice)

            if current_user.is_authenticated:
                invitation = invitation.query.filter_by(
                    user_id=current_user.id, poll_id=poll.id).first()
                if invitation:
                    invitation.vote = vote

            flash(gettext("you have voted."), "success")

            poll.send_watchers("[dudel] new vote: " + poll.title,
                               "email/poll_voted.txt", voter=vote.displayname)

            db.session.commit()

            if current_user.is_authenticated and current_user.autowatch:
                return redirect(url_for("poll_watch", slug=poll.slug, watch="yes", next=poll.get_url()))
            else:
                return redirect(poll.get_url())

    if not request.method == "post":
        poll.fill_vote_form(form)

        for subform in form.vote_choices:
            min_ = poll.amount_minimum or 0
            max_ = poll.amount_maximum or 0
            avg = min_ + (max_ - min_) / 2 if min_ != max_ else 0
            subform.amount.data = avg

    return render_template("poll/vote/edit.jade", poll=poll, form=form)


@app.route("/<slug>/vote/<int:vote_id>/assign", methods=("post", "get"))
@login_required
def poll_vote_assign(slug, vote_id):
    poll = get_poll(slug)
    poll.check_expiry()
    if not poll.user_can_administrate(current_user):
        abort(403)

    vote = vote.query.filter_by(id=vote_id).first_or_404()
    if vote.poll != poll:
        abort(404)
    if vote.user:
        abort(403)

    form = voteassignform()

    if form.validate_on_submit():
        # find the user
        user = user.query.filter(
            func.lower(user.username) == func.lower(form.user.data)).first()
        if not user:
            flash(gettext("the user was not found, please try again."), "error")
            return redirect(url_for("poll_vote_assign", slug=poll.slug, vote_id=vote.id))

        # check for existing votes
        vote_count = vote.query.filter_by(
            poll_id=poll.id, user_id=user.id).count()
        if poll.one_vote_per_user and vote_count > 0:
            flash(gettext("the user has already voted and cannot have multiple votes."), "error")
            return redirect(url_for("poll_vote_assign", slug=poll.slug, vote_id=vote.id))

        # all's right, assign
        vote.user = user
        vote.assigned_by = current_user
        vote.name = ""

        # assign invitation to this vote, if any
        invitation = invitation.query.filter_by(
            user_id=user.id, poll_id=poll.id).first()
        if invitation:
            invitation.vote = vote

        # done.
        db.session.commit()
        flash(gettext("you assigned this vote to %(user)s.", user=user.displayname), "success")
        return redirect(poll.get_url())

    return render_template("poll/vote/assign.jade", poll=poll, vote=vote, form=form)


@app.route("/<slug>/vote/<int:vote_id>/edit", methods=("post", "get"))
def poll_vote_edit(slug, vote_id):
    poll = get_poll(slug)
    poll.check_expiry()

    vote = vote.query.filter_by(id=vote_id).first_or_404()
    if vote.poll != poll:
        abort(404)

    if vote.user and current_user.is_anonymous:
        flash(gettext("this vote was created by a logged in user. if that was you, please log in to edit the vote."),
              "error")
        return redirect(url_for("login", next=url_for("poll_vote_edit", slug=poll.slug, vote_id=vote_id)))

    if vote.user and not current_user.is_anonymous and vote.user != current_user:
        flash(gettext(
            "this vote was created by someone else. you cannot edit their choices."), "error")
        return redirect(poll.get_url())

    form = createvoteform(obj=vote)

    # check if user is logged in
    if (poll.require_login or poll.require_invitation) and current_user.is_anonymous:
        flash(gettext("you need to login to edit votes on this poll."), "error")
        return redirect(url_for("login", next=url_for("poll_vote_edit", slug=poll.slug, vote_id=vote_id)))

    # check if user was invited
    if poll.require_invitation and not current_user.is_invited(poll):
        flash(gettext("you need an invitation to edit votes on this poll."), "error")
        return redirect(poll.get_url())

    if request.method == "post":
        for subform in form.vote_choices:
            subform.value.choices = [(v.id, v.title)
                                     for v in poll.get_choice_values()]

        if form.validate_on_submit():
            if not vote.user:
                vote.name = form.name.data
            vote.anonymous = poll.anonymous_allowed and form.anonymous.data

            if vote.anonymous and not vote.user:
                vote.name = "anonymous"

            vote.comment = form.comment.data

            for subform in form.vote_choices:
                choice = choice.query.filter_by(
                    id=subform.choice_id.data).first()
                value = choicevalue.query.filter_by(
                    id=subform.value.data).first()
                if not choice or choice.poll != poll:
                    abort(404)
                if value and value.poll != poll:
                    abort(404)

                vote_choice = poll.get_vote_choice(vote, choice)
                if not vote_choice:
                    vote_choice = votechoice()
                    vote_choice.vote = vote
                    vote_choice.choice = choice

                vote_choice.comment = subform.comment.data
                vote_choice.amount = subform.amount.data
                vote_choice.value = value

            # remove 'assigned-by' tag if the user themselves edited the vote,
            # and notify them about this change
            if vote.user and vote.user == current_user and vote.assigned:
                vote.assigned_by = none
                flash(gettext(
                    "the vote is not considered \"assigned\" anymore, since you edited it."), "info")

            db.session.commit()
            flash(gettext("the vote has been edited."), "success")
            return redirect(poll.get_url())

    if not request.method == "post":
        poll.fill_vote_form(form)
        for subform in form.vote_choices:
            vote_choice = votechoice.query.filter_by(
                vote_id=vote.id, choice_id=subform.choice_id.data).first()
            subform.comment.data = vote_choice.comment if vote_choice else ""
            subform.amount.data = vote_choice.amount

    return render_template("poll/vote/edit.jade", poll=poll, form=form, vote=vote)


@app.route("/<slug>/vote/<int:vote_id>/delete", methods=("post", "get"))
@csrf.protect()
def poll_vote_delete(slug, vote_id):
    poll = get_poll(slug)
    poll.check_expiry()

    vote = vote.query.filter_by(id=vote_id).first_or_404()
    if vote.poll != poll:
        abort(404)

    if not vote.user_can_delete(current_user):
        abort(403)

    db.session.delete(vote)
    db.session.commit()
    flash(gettext("the vote has been deleted"), "success")
    return redirect(poll.get_url())


@app.route("/<slug>/copy", methods=("post", "get"))
def poll_copy(slug):
    poll = get_poll(slug)

    form = copypollform()
    if form.validate_on_submit():
        new_poll = poll(create_choice_values=not form.copy_choice_values.data)

        # new data
        new_poll.title = form.title.data.strip()
        new_poll.slug = form.slug.data
        new_poll.created = datetime.utcnow()

        # copied data
        new_poll.description = poll.description
        new_poll.type = poll.type
        new_poll.anonymous_allowed = poll.anonymous_allowed
        new_poll.public_listing = poll.public_listing
        new_poll.require_login = poll.require_login
        new_poll.require_invitation = poll.require_invitation
        new_poll.show_results = poll.show_results
        new_poll.one_vote_per_user = poll.one_vote_per_user
        new_poll.allow_comments = poll.allow_comments
        new_poll.show_invitations = poll.show_invitations
        new_poll.owner_id = poll.owner_id

        # copy choice values
        if form.copy_choice_values.data:
            new_poll.choice_values = []
            for choice_value in poll.choice_values:
                new_choice_value = choice_value.copy()
                new_choice_value.poll = new_poll

        # copy invitations
        invitation_users = []
        if form.copy_invitations:
            invitation_users.extend(
                [invitation.user for invitation in poll.invitations])

        # create invitations from votes
        if form.create_invitations_from_votes.data:
            invitation_users.extend([vote.user for vote in poll.votes])

        # copy choices
        if form.copy_choices.data:
            date_offset = none
            if poll.type in (polltype.datetime, polltype.date):
                date_offset = timedelta(days=form.date_offset.data)

            for choice in poll.choices:
                new_choice = choice.copy()
                new_choice.poll = new_poll
                if date_offset and new_choice.date:
                    new_choice.date += date_offset

        # copy watchers
        for watch in poll.watchers:
            new_watch = watch.copy()
            new_watch.poll = new_poll

        # reset owneship if desired
        if form.reset_ownership.data:
            new_poll.owner = none

        db.session.add(new_poll)
        flash(gettext("the poll was copied."), "success")

        # perform invitations
        invited, failed = new_poll.invite_all(invitation_users)
        if invited:
            flash(gettext("you have invited %(count)d users.", count=len(invited)), "success")
        if failed:
            flash(gettext("%(count)d users could not be invited.", count=len(failed)), "info")

        db.session.commit()
        return redirect(new_poll.get_url())

    elif request.method == "get":
        form.title.data = gettext("copy of %(title)s", title=poll.title)
        form.reset_ownership.data = not poll.user_can_administrate(
            current_user)

    return render_template("poll/settings/copy.jade", poll=poll, form=form)


@app.errorhandler(pollexpiredexception)
def poll_expired(e):
    flash(gettext("this poll is expired. you cannot vote or edit your choice anymore."), "error")
    return redirect(e.poll.get_url())


@app.errorhandler(pollactionexception)
def poll_action(e):
    if current_user.is_anonymous:
        flash(gettext("you do not have permission to %(action)s this poll. please log in and try again.",
                      action=e.action), "error")
        return redirect(url_for("login", next=request.url))
    else:
        flash(gettext(
            "you do not have permission to %(action)s this poll.", action=e.action), "error")
        return redirect(e.poll.get_url())


@app.route('/static/translations/<locale>.po')
def root(locale):
    if locale not in ("de",):
        abort(404)
    return open('dudel/translations/%s/lc_messages/messages.po' % locale).read()
