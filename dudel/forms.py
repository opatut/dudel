from dudel import app
from flask import request, Markup
from flask.ext.babel import gettext, lazy_gettext
from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms import ValidationError
from wtforms.fields import TextField, SelectField, BooleanField, HiddenField, FieldList, FormField, RadioField, PasswordField, TextAreaField
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.validators import Required, Length, Regexp, Optional, NoneOf
from dudel.models import Poll, update_user_data
import ldap
from ldap.dn import escape_dn_chars
from datetime import datetime

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
    def __init__(self, type, column, message = lazy_gettext("This entry already exists.")):
        self.type = type
        self.column = column
        self.message = message
        self.allowed_objects = []

    def __call__(self, form, field):
        if len([x for x in self.type.query.filter_by(**{self.column:field.data.strip()}).all() if not x in self.allowed_objects]):
            raise ValidationError(self.message)

class LDAPAuthenticator(object):
    def __init__(self, username_value_or_field, message = lazy_gettext("Invalid credentials.")):
        self.username_value_or_field = username_value_or_field
        self.message = message

    def __call__(self, form, field):
        username = self.username_value_or_field
        if self.username_value_or_field in form.data:
            username = form.data[self.username_value_or_field]

        if app.config["LDAP_DEBUG_MODE"]:
            if username != app.config["LDAP_DEBUG_DATA"]["uid"] or  app.config["LDAP_DEBUG_PASSWORD"] != field.data:
                raise ValidationError("LDAP_DEBUG_PASSWORD set but incorrect, log in as %s, password %s." %
                        (app.config["LDAP_DEBUG_DATA"]["uid"], app.config["LDAP_DEBUG_PASSWORD"]))
            else:
                update_user_data(username, app.config["LDAP_DEBUG_DATA"])
                return

        try:
            connection = ldap.initialize(app.config["LDAP_SERVER"])

            # At this point, we update the user info (since we already have
            # a connection to LDAP)
            #connection.start_tls_s()
            escaped_username = escape_dn_chars(username)
            connection.simple_bind_s(app.config["LDAP_BIND_DN"].format(uid=escaped_username), field.data)
            filter = app.config["LDAP_FILTER"].format(uid=escaped_username)
            base_dn = app.config["LDAP_BASE_DN"].format(uid=escaped_username)
            results = connection.search_s(base_dn, ldap.SCOPE_SUBTREE, filter)
            results = {k:(v if len(v)>1 else v[0]) for k,v in results[0][1].iteritems()}
            connection.unbind_s()

            update_user_data(username, results)

        except ldap.INVALID_CREDENTIALS:
            raise ValidationError(self.message)
        except ldap.LDAPError, e:
            raise ValidationError("LDAP Error: " + (e.message["desc"] if e.message else "%s (%s)"%(e[1],e[0])))

class SelectButtonInput:
    def __call__(self, field, **kwargs):
        return Markup('<button name="%s" type="submit" value="%s" class="btn-link">%s</button>'
                        % (field.name, field.data, field.label.text))

class YourNameRequired(object):
    def __call__(self, form, field):
        if form["anonymous"].data:
            return # nevermind if we are anonymous!
        if not field.data and current_user.is_anonymous():
            raise ValidationError(gettext("This field is required."))

class RequiredIfAnonymous(object):
    def __call__(self, form, field):
        if not field.data and current_user.is_anonymous():
            raise ValidationError(gettext("This field is required."))

class AtLeastNow(object):
    def __call__(self, form, field):
        if field.data < datetime.utcnow():
            raise ValidationError(gettext("Please select a date later than right now."))

################################################################################

class CreatePollForm(Form):
    title = TextField(lazy_gettext("Title"), validators=[Required(), Length(min=3, max=80)])
    type = SelectField(lazy_gettext("Type"), choices=[("date", lazy_gettext("Schedule a meeting")), ("normal", lazy_gettext("Normal poll"))])
    slug = TextField(lazy_gettext("URL name"), validators=[Required(),
        Length(min=3, max=80),
        Regexp(r"^[a-zA-Z0-9_-]*$", message=lazy_gettext("Invalid character.")),
        UniqueObject(Poll, "slug", message=lazy_gettext("A poll with this URL name already exists.")),
        NoneOf(Poll.RESERVED_NAMES, message=lazy_gettext("This is a reserved name."))
        ])
    due_date = DateTimeField(lazy_gettext("Due date"), validators=[Optional()])

class DateTimeSelectForm(Form):
    dates = TextField(lazy_gettext("Dates"), validators = [Regexp("([\d]{4}-[\d]{2}-[\d]{2},?)*")])
    times = TextField(lazy_gettext("Times"), validators = [Regexp("([\d]{2}:[\d]{2}(:[\d]{2})?,?)*")])

class AddChoiceForm(MultiForm):
    text = TextField(lazy_gettext("Choice"), validators=[Required(), Length(max=80)])

class EditChoiceForm(MultiForm):
    text = TextField(lazy_gettext("Choice"), validators=[Required(), Length(max=80)])

class AddValueForm(MultiForm):
    title = TextField(lazy_gettext("Title"), validators=[Required(), Length(max=80)])
    color = TextField(lazy_gettext("Color"), validators=[Required(), Regexp("^#?([0-9A-Fa-f]{3}){1,2}$")])
    icon = TextField(lazy_gettext("Icon"), validators=[Required(), Length(max=80)], default="question")

class LoginForm(MultiForm):
    username = TextField(lazy_gettext("Username"), validators=[Required()])
    password = PasswordField(lazy_gettext("Password"), validators=[Required(), LDAPAuthenticator("username")])

class EditPollForm(Form):
    title = TextField(lazy_gettext("Title"), validators=[Required(), Length(min=3, max=80)])
    description = TextAreaField(lazy_gettext("Description"))
    due_date = DateTimeField(lazy_gettext("Due date"), validators=[Optional(), AtLeastNow()])
    anonymous_allowed = BooleanField(lazy_gettext("Allow anonymous votes"))
    require_login = BooleanField(lazy_gettext("Require login to vote"))
    public_listing = BooleanField(lazy_gettext("Show in public poll list"))
    one_vote_per_user = BooleanField(lazy_gettext("One vote per user (only effective with) login)"))
    allow_comments = BooleanField(lazy_gettext("Allow comments"))
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
    comment = TextField(lazy_gettext("Comment"))
    choice_id = HiddenField("choice id", validators=[Required()])

class CreateVoteForm(Form):
    name = TextField(lazy_gettext("Your Name"), validators=[YourNameRequired(), Length(max=80)])
    anonymous = BooleanField(lazy_gettext("Post anonymous vote"))
    vote_choices = FieldList(FormField(CreateVoteChoiceForm))

class PollPassword(Form):
    password = PasswordField(lazy_gettext("Poll password"), validators=[Required()])

class CommentForm(Form):
    name = TextField(lazy_gettext("Your Name"), validators=[RequiredIfAnonymous(), Length(max=80)])
    text = TextAreaField(lazy_gettext("Comment"))

class LanguageForm(Form):
    lang = SelectField(lazy_gettext("Language"), choices=[
        ('en', 'English'),
        ('de', 'Deutsch')],
    option_widget=SelectButtonInput())
