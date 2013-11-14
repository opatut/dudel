from dudel import app
from flask import request
from flask.ext.wtf import Form
from wtforms import ValidationError
from wtforms.fields import TextField, SelectField, BooleanField, TextAreaField, HiddenField, PasswordField
from wtforms.ext.dateutil.fields import DateField, DateTimeField
from wtforms.validators import Required, Length, Regexp, Optional
from dudel.models import *
import ldap

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
    def __init__(self, type, column, message = "This entry already exists."):
        self.type = type
        self.column = column
        self.message = message
        self.allowed_objects = []

    def __call__(self, form, field):
        if len([x for x in self.type.query.filter_by(**{self.column:field.data.strip()}).all() if not x in self.allowed_objects]):
            raise ValidationError(self.message)

class LDAPAuthenticator(object):
    def __init__(self, username_value_or_field, message = "Invalid credentials."):
        self.username_value_or_field = username_value_or_field
        self.message = message

    def __call__(self, form, field):
        username = self.username_value_or_field
        if self.username_value_or_field in form.data: username = form.data[self.username_value_or_field]

        if app.config["LDAP_DEBUG_MODE"]:
            if username != app.config["LDAP_DEBUG_DATA"]["uid"] or  app.config["LDAP_DEBUG_PASSWORD"] != field.data:
                raise ValidationError("LDAP_DEBUG_PASSWORD set but incorrect, log in as %s, password %s." %
                        (app.config["LDAP_DEBUG_DATA"]["uid"], app.config["LDAP_DEBUG_PASSWORD"]))
            else:
                update_user_data(username, app.config["LDAP_DEBUG_DATA"])
                return

        try:
            with ldap.initialize(app.config["LDAP_SERVER"]) as connection:
                #connection.start_tls_s()
                connection.simple_bind_s(app.config["LDAP_DN"] % username, field.data)

                # At this point, we update the user info (since we already have
                # a connection to LDAP)
                update_user_data(username, {}) #TODO

        except ldap.INVALID_CREDENTIALS:
            raise ValidationError(self.message)
        except ldap.LDAPError, e:
            raise ValidationError("LDAP Error: " + (e.message["desc"] if e.message else "%s (%s)"%(e[1],e[0])))

################################################################################

class CreatePollForm(Form):
    title = TextField("Title", validators=[Required(), Length(min=3)])
    type = SelectField("Type", choices=[("date", "Schedule a meeting"), ("normal", "Normal poll")])
    slug = TextField("URL name", validators=[Required(),
        Length(min=3),
        Regexp(r"^[a-zA-Z0-9_-]*$", message="Invalid character."),
        UniqueObject(Poll, "slug", message="A poll with this URL name already exists.")
        ])
    due_date = DateTimeField("Due date", validators=[Optional()])

class AddDateForm(MultiForm):
    date = DateField("Date", validators=[Required()])

class AddTimeForm(MultiForm):
    time = TextField("Time", validators=[Required(), Regexp(r"^\d?\d(:\d\d)?$", message="Invalid time format (HH:MM).")])

class AddChoiceForm(MultiForm):
    text = TextField("Choice", validators=[Required(), Length(min=1)])

class LoginForm(MultiForm):
    username = TextField("Username", validators=[Required()])
    password = PasswordField("Password", validators=[Required(), LDAPAuthenticator("username")])

class EditPollForm(Form):
    title = TextField("Title", validators=[Required(), Length(min=3)])
    due_date = DateTimeField("Due date", validators=[Optional()])
    anonymous_allowed = BooleanField("Allow anonymous votes")
    require_login = BooleanField("Require login to vote")
    public_listing = BooleanField("Show in public poll list")
    password = TextField("Password")
    password_mode = SelectField("Password mode", choices=[("none", "Do not use password"), ("show", "Password required to show poll"), ("vote", "Password required to vote")])
    show_results = SelectField("Results display", choices=[
        ("complete", "show all votes"),
        ("summary", "show only summary"),
        ("never", "Do not show results"),
        ("complete_after_vote", "Show all votes, but only after voting"),
        ("summary_after_vote", "Show summary, but only after voting")])
    send_mail = BooleanField("Send mail to participants about results")
