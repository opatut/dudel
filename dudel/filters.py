from dudel import app, ICONS
from dudel.forms import LoginForm
from flask import g

@app.template_filter()
def date(s):
    return s.strftime("%a %d %b")

@app.template_filter()
def time(s):
    return s.strftime("%H:%M")

@app.template_filter()
def datetime(s):
    return s.strftime("%a %d %b %H:%M")

@app.context_processor
def inject():
    return dict(
        ICONS=ICONS,
        login_form=LoginForm()
        )

