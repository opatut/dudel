# from flask import request, Markup
# from flask_wtf import FlaskForm as Form
# from flask.ext.login import current_user
#
# from pytz import common_timezones
#
# from wtforms.fields import TextField, SelectField, BooleanField, HiddenField, \
#     FieldList, FormField, RadioField, PasswordField, TextAreaField, \
#     DecimalField, IntegerField
# from wtforms.ext.dateutil.fields import DateTimeField
# from wtforms.validators import Required, Length, Regexp, Optional, NoneOf, \
#     EqualTo, Email, ValidationError, StopValidation
#
# from dudel import app
# from dudel.login import try_login
# from dudel.models.poll import Poll, PollType
# from dudel.models.group import Group
# from dudel.util import random_string, get_slug

#
# # Helper class for multiple forms on one page
# class MultiForm(Form):
#     form_name = HiddenField("form name", validators=[Required()])
#
#     def __init__(self, *args, **kwargs):
#         self._form_name = type(self).__name__
#         Form.__init__(self, *args, **kwargs)
#
#     def is_submitted(self):
#         return Form.is_submitted(self) and request.form.get("form_name") == self._form_name
#
#     def hidden_tag(self, *args, **kwargs):
#         self.form_name.data = self._form_name
#         return Form.hidden_tag(self, *args, **kwargs)
#
#
# class UniqueObject(object):
#     def __init__(self, type, column, constraint={}, message="This entry already exists."):
#         self.type = type
#         self.column = column
#         self.message = message
#         self.constraint = constraint
#         self.allowed_objects = []
#
#     def __call__(self, form, field):
#         c = self.constraint
#         c[self.column] = field.data.strip()
#
#         if len([x for x in self.type.query.filter_by(**c).all() if not x in self.allowed_objects]):
#             raise ValidationError(self.message)
#
#
# class CustomAuthenticator(object):
#     def __init__(self, username_value_or_field, message="Invalid credentials."):
#         self.username_value_or_field = username_value_or_field
#         self.message = message
#
#     def __call__(self, form, field):
#         username = self.username_value_or_field
#         if self.username_value_or_field in form.data:
#             username = form.data[self.username_value_or_field]
#
#         user, error = try_login(username, field.data)
#         # Unexpected error
#         if error:
#             raise ValidationError(error)
#         # No login provider accepts
#         if not user:
#             raise ValidationError(self.message)
#
#
# class SelectButtonInput:
#     def __call__(self, field, **kwargs):
#         return Markup('<button name="%s" type="submit" value="%s" class="btn-link">%s</button>'
#                       % (field.name, field.data, field.label.text))
#
#
# class RequiredIf(object):
#     def __init__(self, condition):
#         self.condition = condition
#
#     def __call__(self, form, field):
#         if self.condition(form, field) and not field.data:
#             raise ValidationError("This field is required.")
#
#
# class OptionalIf(object):
#     def __init__(self, condition):
#         self.condition = condition
#
#     def __call__(self, form, field):
#         if self.condition(form, field) and not field.data:
#             field.errors[:] = []
#             print("This is optional because of condition")
#             raise StopValidation()
#
# class SlugGenerator(object):
#     def __init__(self, title_field):
#         self.title_field = title_field
#         self.message_in_use = "This slug is already in use."
#
#     def __call__(self, form, field):
#         slug = field.data.strip()
#
#         def generate(iteration=0):
#             if app.config["RANDOM_SLUGS"]:
#                 return random_string()
#             else:
#                 title = form[self.title_field].data.strip()
#                 if iteration > 0:
#                     title += " %s" % (iteration + 1)
#                 return get_slug(title)
#
#         # no custom slugs allowed
#         # -> generate until valid slug found
#         if not app.config["ALLOW_CUSTOM_SLUGS"]:
#             i = 0
#             while True:
#                 slug = generate(i)
#                 if not Poll.query.filter_by(slug=slug, deleted=False).first():
#                     break
#                 i += 1
#
#         # no slug entered, but customization allowed
#         # -> generate once, fail if in use and show form field
#         elif not slug:
#             slug = generate()
#
#         field.data = slug
#
#
#
# # ###############################################################################
#
# class PollForm(MultiForm):
#     title = TextField("Title", validators=[Required(), Length(min=3, max=80)])
#     slug = TextField("URL name", validators=[SlugGenerator("title"),
#                                                            Length(min=3, max=80),
#                                                            Regexp(r"^[a-zA-Z0-9_-]*$",
#                                                                   message="Invalid character."),
#                                                            UniqueObject(Poll, "slug", dict(deleted=False),
#                                                                         message="A poll with this URL name already exists."),
#                                                            NoneOf(Poll.RESERVED_NAMES,
#                                                                   message="This is a reserved name.")
#     ])
#
#
# class CreatePollForm(PollForm):
#     type = SelectField("Type",
#                        choices=[(choice.value, choice) for choice in PollType])
#     visibility = SelectField("Visibility",
#                              choices=[("public", "Public"), ("hidden", "Hidden")],
#                              default="hidden")
#
# class CreateGroupForm(Form):
#     name = TextField("Name", validators=[
#         Required(),
#         Length(min=3, max=80),
#         UniqueObject(Group, "name", message="A group with this name already exists.")
#     ])
#
#
# class CopyPollForm(PollForm):
#     copy_choices = BooleanField("Copy choices", default=True)
#     copy_invitations = BooleanField("Copy invitations", default=True)
#     copy_choice_values = BooleanField("Copy possible answer values", default=True)
#     date_offset = IntegerField("Date shift (days)", default=0)
#     create_invitations_from_votes = BooleanField("Create invitations from votes", default=False)
#     reset_ownership = BooleanField("Reset ownership", default=True)
#
#
# class DateTimeSelectForm(Form):
#     dates = TextField("Dates", validators=[Regexp("^([\d]{4}-[\d]{2}-[\d]{2},?)*$")])
#     times = TextField("Times", validators=[Regexp("^([\d]{2}:[\d]{2}(:[\d]{2})?,?)*$")])
#
#
# class AddChoiceForm(MultiForm):
#     text = TextField("Choice", validators=[Required(), Length(max=80)])
#
#
# class EditChoiceForm(MultiForm):
#     text = TextField("Choice", validators=[Required(), Length(max=80)])
#
#
# class AddValueForm(MultiForm):
#     title = TextField("Title", validators=[Required(), Length(max=80)])
#     color = TextField("Color", validators=[Required(), Regexp("^#?([0-9A-Fa-f]{3}){1,2}$")])
#     icon = TextField("Icon", validators=[Required(), Length(max=80)], default="question")
#     weight = DecimalField("Weight", validators=[], default=0)
#
#
# class LoginForm(MultiForm):
#     username = TextField("Username", validators=[Required()])
#     password = PasswordField("Password", validators=[Required(), CustomAuthenticator("username")])
#
#
# class RegisterForm(MultiForm):
#     username = TextField("Username", validators=[Required()])
#     firstname = TextField("First name")
#     lastname = TextField("Last name")
#     password1 = PasswordField("Password", validators=[Required(), Length(min=4)])
#     password2 = PasswordField("Password again", validators=[Required(), EqualTo("password1")])
#     email = TextField("Email", validators=[Required(), Email()])
#
#
# class SettingsForm(MultiForm):
#     preferred_language = SelectField("Language", choices=LANGUAGES)
#     timezone_name = SelectField("Timezone",
#                                 choices=[("", "Server default")] + [(c, c) for c in common_timezones])
#     autowatch = BooleanField("Auto-watch polls")
#     allow_invitation_mails = BooleanField("Allow to receive emails for poll invitations")
#
#
# class SettingsFormPassword(SettingsForm):
#     firstname = TextField("First name")
#     lastname = TextField("Last name")
#     password1 = PasswordField("Password", validators=[Optional(), Length(min=4)])
#     password2 = PasswordField("Password again", validators=[EqualTo("password1")])
#     email = TextField("Email", validators=[Required(), Email()])
#
#
# class SettingsFormLdap(SettingsForm):
#     pass
#
#
# class EditPollForm(Form):
#     title = TextField("Title", validators=[Required(), Length(min=3, max=80)])
#     description = TextAreaField("Description")
#     due_date = DateTimeField("Due date", validators=[Optional()])
#     anonymous_allowed = BooleanField("Allow anonymous votes")
#     require_login = BooleanField("Require login to vote")
#     require_invitation = BooleanField("Require invitation to vote (requires login)")
#     public_listing = BooleanField("Show in public poll list")
#     one_vote_per_user = BooleanField("One vote per user (only effective with login)")
#     allow_comments = BooleanField("Allow comments")
#     show_invitations = BooleanField("Show invitations as empty votes")
#     owner_id = SelectField("Ownership", choices=[(0, "Nobody")], coerce=int)
#     timezone_name = SelectField("Timezone",
#                                 choices=[("", "Coordinated time")] + [(c, c) for c in common_timezones])
#     # password = TextField("Password")
#     # password_level = SelectField("Password mode", choices=[
#     #     (0, "Do not use password"),
#     #     (1, "Password required for editing"),
#     #     (2, "Password required to vote"),
#     #     (3, "Password required to show poll")],
#     #     coerce=int)
#     show_results = SelectField("Results display", choices=[
#         ("complete", "show all votes"),
#         ("summary", "show only summary"),
#         ("never", "Do not show results"),
#         ("complete_after_vote", "Show all votes, but only after voting"),
#         ("summary_after_vote", "Show summary, but only after voting")])
#     send_mail = BooleanField("Send mail to participants about results")
#
#
# class CreateVoteChoiceForm(Form):
#     value = RadioField("Value", coerce=int, validators=[Optional()])
#     amount = DecimalField("Amount", validators=[Optional()], default=0)
#     comment = TextField("Comment")
#     choice_id = HiddenField("choice id", validators=[Required()])
#
# class AmountRangeForm(Form):
#     minimum = DecimalField("Minimum")
#     maximum = DecimalField("Maximum")
#     step = DecimalField("Step")
#
# def anonymous_not_checked(form, field):
#     return not form["anonymous"].data
#
#
# def logged_in(form, field):
#     return current_user.is_authenticated()
#
#
# def not_logged_in(form, field):
#     return current_user.is_anonymous()
#
#
# class CreateVoteForm(Form):
#     name = TextField("Your Name", validators=[RequiredIf(anonymous_not_checked), Length(max=80)])
#     anonymous = BooleanField("Post anonymous vote")
#     vote_choices = FieldList(FormField(CreateVoteChoiceForm))
#     comment = TextAreaField("Comment", validators=[Optional()])
#
#
# class PollPassword(Form):
#     password = PasswordField("Poll password", validators=[Required()])
#
#
# class CommentForm(Form):
#     name = TextField("Your Name", validators=[RequiredIf(not_logged_in), Length(max=80)])
#     text = TextAreaField("Comment")
#
# class LanguageForm(Form):
#     language = SelectField("Language", choices=LANGUAGES, option_widget=SelectButtonInput())
#
#
# class PollInviteForm(Form):
#     member = TextField("Group or User")
#
#
# class GroupAddMemberForm(Form):
#     member = TextField("User")
#
#
# class VoteAssignForm(Form):
#     user = TextField("New vote owner")
