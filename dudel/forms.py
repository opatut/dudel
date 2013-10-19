from flask.ext.wtf import Form
from wtforms.fields import TextField, SelectField, BooleanField, TextAreaField
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.validators import Required, Length, Regexp, Optional

class CreatePollForm(Form):
    title = TextField("Title", validators=[Required(), Length(min=3)])
    type = SelectField("Type", choices=[("date", "Schedule a meeting"), ("normal", "Normal poll")])
    slug = TextField("URL name", validators=[Required(), Length(min=3), Regexp(r"^[a-zA-Z0-9_-]*$", message="Invalid character.")])
    due_date = DateTimeField("Due date", validators=[Optional()])
