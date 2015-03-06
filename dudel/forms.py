from flask import request, Markup
from flask.ext.babel import gettext, lazy_gettext
from flask.ext.wtf import Form, RecaptchaField
from flask.ext.wtf.recaptcha.validators import Recaptcha as RecaptchaValidator
from flask.ext.login import current_user

from wtforms.fields import TextField, SelectField, BooleanField, HiddenField, FieldList, FormField, RadioField, \
    PasswordField, TextAreaField, DecimalField, IntegerField
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.validators import Required, Length, Regexp, Optional, NoneOf, EqualTo, Email, ValidationError, \
    StopValidation

from pytz import common_timezones

from dudel import default_timezone
from dudel.models.poll import Poll, PollType
from dudel.models.group import Group
from dudel.login import try_login


LANGUAGES = [('en', 'English'), ('de', 'Deutsch')]


# Helper class for multiple forms on one page
class MultiForm(Form):
    form_name = HiddenField("form name", validators=[Required()])

    def __init__(self, *args, **kwargs):
        self._form_name = type(self).__name__
        Form.__init__(self, *args, **kwargs)

    def is_submitted(self):
        return Form.is_submitted(self) and request.form.get("form_name") == self._form_name

    def hidden_tag(self, *args, **kwargs):
        self.form_name.data = self._form_name
        return Form.hidden_tag(self, *args, **kwargs)


class UniqueObject(object):
    def __init__(self, type, column, constraint={}, message=lazy_gettext("This entry already exists.")):
        self.type = type
        self.column = column
        self.message = message
        self.constraint = constraint
        self.allowed_objects = []

    def __call__(self, form, field):
        c = self.constraint
        c[self.column] = field.data.strip()

        if len([x for x in self.type.query.filter_by(**c).all() if not x in self.allowed_objects]):
            raise ValidationError(self.message)


class CustomAuthenticator(object):
    def __init__(self, username_value_or_field, message=lazy_gettext("Invalid credentials.")):
        self.username_value_or_field = username_value_or_field
        self.message = message

    def __call__(self, form, field):
        username = self.username_value_or_field
        if self.username_value_or_field in form.data:
            username = form.data[self.username_value_or_field]

        user, error = try_login(username, field.data)
        # Unexpected error
        if error:
            raise ValidationError(error)
        # No login provider accepts
        if not user:
            raise ValidationError(self.message)


class SelectButtonInput:
    def __call__(self, field, **kwargs):
        return Markup('<button name="%s" type="submit" value="%s" class="btn-link">%s</button>'
                      % (field.name, field.data, field.label.text))


class RequiredIf(object):
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, form, field):
        if self.condition(form, field) and not field.data:
            raise ValidationError(gettext("This field is required."))


class OptionalIf(object):
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, form, field):
        if self.condition(form, field) and not field.data:
            field.errors[:] = []
            print("This is optional because of condition")
            raise StopValidation()


# ###############################################################################

class PollForm(MultiForm):
    title = TextField(lazy_gettext("Title"), validators=[Required(), Length(min=3, max=80)])
    slug = TextField(lazy_gettext("URL name"), validators=[Optional(),
                                                           Length(min=3, max=80),
                                                           Regexp(r"^[a-zA-Z0-9_-]*$",
                                                                  message=lazy_gettext("Invalid character.")),
                                                           UniqueObject(Poll, "slug", dict(deleted=False),
                                                                        message=lazy_gettext(
                                                                            "A poll with this URL name already exists.")),
                                                           NoneOf(Poll.RESERVED_NAMES,
                                                                  message=lazy_gettext("This is a reserved name."))
    ])


class CreatePollForm(PollForm):
    type = SelectField(lazy_gettext("Type"),
                       choices=[(choice.value, choice) for choice in PollType])


class CreateGroupForm(Form):
    name = TextField(lazy_gettext("Name"), validators=[
        Required(),
        Length(min=3, max=80),
        UniqueObject(Group, "name", message=lazy_gettext("A group with this name already exists."))
    ])


class CopyPollForm(PollForm):
    copy_choices = BooleanField(lazy_gettext("Copy choices"), default=True)
    copy_invitations = BooleanField(lazy_gettext("Copy invitations"), default=True)
    copy_choice_values = BooleanField(lazy_gettext("Copy possible answer values"), default=True)
    date_offset = IntegerField(lazy_gettext("Date shift (days)"), default=0)
    create_invitations_from_votes = BooleanField(lazy_gettext("Create invitations from votes"), default=False)
    reset_ownership = BooleanField(lazy_gettext("Reset ownership"), default=True)


class DateTimeSelectForm(Form):
    dates = TextField(lazy_gettext("Dates"), validators=[Regexp("^([\d]{4}-[\d]{2}-[\d]{2},?)*$")])
    times = TextField(lazy_gettext("Times"), validators=[Regexp("^([\d]{2}:[\d]{2}(:[\d]{2})?,?)*$")])


class AddChoiceForm(MultiForm):
    text = TextField(lazy_gettext("Choice"), validators=[Required(), Length(max=80)])


class EditChoiceForm(MultiForm):
    text = TextField(lazy_gettext("Choice"), validators=[Required(), Length(max=80)])


class AddValueForm(MultiForm):
    title = TextField(lazy_gettext("Title"), validators=[Required(), Length(max=80)])
    color = TextField(lazy_gettext("Color"), validators=[Required(), Regexp("^#?([0-9A-Fa-f]{3}){1,2}$")])
    icon = TextField(lazy_gettext("Icon"), validators=[Required(), Length(max=80)], default="question")
    weight = DecimalField(lazy_gettext("Weight"), validators=[], default=0)


class LoginForm(MultiForm):
    username = TextField(lazy_gettext("Username"), validators=[Required()])
    password = PasswordField(lazy_gettext("Password"), validators=[Required(), CustomAuthenticator("username")])


class RegisterForm(MultiForm):
    username = TextField(lazy_gettext("Username"), validators=[Required()])
    firstname = TextField(lazy_gettext("First name"))
    lastname = TextField(lazy_gettext("Last name"))
    password1 = PasswordField(lazy_gettext("Password"), validators=[Required(), Length(min=4)])
    password2 = PasswordField(lazy_gettext("Password again"), validators=[Required(), EqualTo("password1")])
    email = TextField(lazy_gettext("Email"), validators=[Required(), Email()])


class SettingsForm(MultiForm):
    preferred_language = SelectField(lazy_gettext("Language"), choices=LANGUAGES)
    timezone_name = SelectField(lazy_gettext("Timezone"),
                                choices=[("",
                                          lazy_gettext("Server default (%(timezone)s)", timezone=default_timezone))] + [
                                            (c, c) for c in common_timezones])
    autowatch = BooleanField(lazy_gettext("Auto-watch polls"))
    allow_invitation_mails = BooleanField(lazy_gettext("Allow to receive emails for poll invitations"))


class SettingsFormPassword(SettingsForm):
    firstname = TextField(lazy_gettext("First name"))
    lastname = TextField(lazy_gettext("Last name"))
    password1 = PasswordField(lazy_gettext("Password"), validators=[Optional(), Length(min=4)])
    password2 = PasswordField(lazy_gettext("Password again"), validators=[EqualTo("password1")])
    email = TextField(lazy_gettext("Email"), validators=[Required(), Email()])


class SettingsFormLdap(SettingsForm):
    pass


class EditPollForm(Form):
    title = TextField(lazy_gettext("Title"), validators=[Required(), Length(min=3, max=80)])
    description = TextAreaField(lazy_gettext("Description"))
    due_date = DateTimeField(lazy_gettext("Due date"), validators=[Optional()])
    anonymous_allowed = BooleanField(lazy_gettext("Allow anonymous votes"))
    require_login = BooleanField(lazy_gettext("Require login to vote"))
    require_invitation = BooleanField(lazy_gettext("Require invitation to vote (requires login)"))
    public_listing = BooleanField(lazy_gettext("Show in public poll list"))
    one_vote_per_user = BooleanField(lazy_gettext("One vote per user (only effective with login)"))
    allow_comments = BooleanField(lazy_gettext("Allow comments"))
    show_invitations = BooleanField(lazy_gettext("Show invitations as empty votes"))
    owner_id = SelectField(lazy_gettext("Ownership"), choices=[(0, "Nobody")], coerce=int)
    timezone_name = SelectField(lazy_gettext("Timezone"),
                                choices=[("", lazy_gettext("Coordinated time"))] + [(c, c) for c in common_timezones])
    # password = TextField("Password")
    # password_level = SelectField("Password mode", choices=[
    #     (0, "Do not use password"),
    #     (1, "Password required for editing"),
    #     (2, "Password required to vote"),
    #     (3, "Password required to show poll")],
    #     coerce=int)
    show_results = SelectField(lazy_gettext("Results display"), choices=[
        ("complete", lazy_gettext("show all votes")),
        ("summary", lazy_gettext("show only summary")),
        ("never", lazy_gettext("Do not show results")),
        ("complete_after_vote", lazy_gettext("Show all votes, but only after voting")),
        ("summary_after_vote", lazy_gettext("Show summary, but only after voting"))])
    send_mail = BooleanField(lazy_gettext("Send mail to participants about results"))


class CreateVoteChoiceForm(Form):
    value = RadioField(lazy_gettext("Value"), coerce=int, validators=[Optional()])
    amount = DecimalField(lazy_gettext("Amount"), validators=[Optional()], default=0)
    comment = TextField(lazy_gettext("Comment"))
    choice_id = HiddenField("choice id", validators=[Required()])

class AmountRangeForm(Form):
    minimum = DecimalField(lazy_gettext("Minimum"))
    maximum = DecimalField(lazy_gettext("Maximum"))
    step = DecimalField(lazy_gettext("Step"))

def anonymous_not_checked(form, field):
    return not form["anonymous"].data


def logged_in(form, field):
    return current_user.is_authenticated()


def not_logged_in(form, field):
    return current_user.is_anonymous()


class CreateVoteForm(Form):
    name = TextField(lazy_gettext("Your Name"), validators=[RequiredIf(anonymous_not_checked), Length(max=80)])
    anonymous = BooleanField(lazy_gettext("Post anonymous vote"))
    vote_choices = FieldList(FormField(CreateVoteChoiceForm))
    comment = TextAreaField(lazy_gettext("Comment"), validators=[Optional()])


class PollPassword(Form):
    password = PasswordField(lazy_gettext("Poll password"), validators=[Required()])


class CommentForm(Form):
    name = TextField(lazy_gettext("Your Name"), validators=[RequiredIf(not_logged_in), Length(max=80)])
    text = TextAreaField(lazy_gettext("Comment"))
    captcha = RecaptchaField(validators=[OptionalIf(logged_in), RecaptchaValidator()])


class LanguageForm(Form):
    language = SelectField(lazy_gettext("Language"), choices=LANGUAGES, option_widget=SelectButtonInput())


class PollInviteForm(Form):
    member = TextField(lazy_gettext("Group or User"))


class GroupAddMemberForm(Form):
    member = TextField(lazy_gettext("User"))


class VoteAssignForm(Form):
    user = TextField(lazy_gettext("New vote owner"))
