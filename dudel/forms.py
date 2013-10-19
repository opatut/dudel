from flask import request
from flask.ext.wtf import Form
from wtforms.fields import TextField, SelectField, BooleanField, TextAreaField, HiddenField
from wtforms.ext.dateutil.fields import DateField, DateTimeField
from wtforms.validators import Required, Length, Regexp, Optional

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

################################################################################

class CreatePollForm(Form):
    title = TextField("Title", validators=[Required(), Length(min=3)])
    type = SelectField("Type", choices=[("date", "Schedule a meeting"), ("normal", "Normal poll")])
    slug = TextField("URL name", validators=[Required(), Length(min=3), Regexp(r"^[a-zA-Z0-9_-]*$", message="Invalid character.")])
    due_date = DateTimeField("Due date", validators=[Optional()])

class AddDateForm(MultiForm):
    date = DateField("Date", validators=[Required()])

class AddTimeForm(MultiForm):
    time = TextField("Time", validators=[Required(), Regexp(r"^\d?\d(:\d\d)?$", message="Invalid time format (HH:MM).")])
