from dudel import app, ICONS
from dudel.models import Choice
from dudel.forms import LoginForm, LanguageForm
from flask import g
from flask.ext.babel import format_date, format_time, get_locale
from json import dumps
import datetime as dt

date_formats = {'de': 'EEE, dd. MMM'}

@app.template_filter()
def date(s, rebase=True, year=False):
    return format_date(s,
                       date_formats.get(get_locale().language, 'EEE, dd MMM') + (' yyyy' if year else ''),
                       rebase=rebase)

@app.template_filter()
def time(s, rebase=True):
    return format_time(s, 'HH:mm', rebase=rebase)

@app.template_filter()
def datetime(s, rebase=True):
    return date(s, rebase) + ', ' + time(s, rebase)

@app.template_filter()
def json(s):
    return dumps(s)

@app.template_filter()
def group_title(title):
    if isinstance(title, dt.date):
        return date(title)
    elif isinstance(title, dt.time):
        return time(title)
    else:
        return title

@app.template_filter()
def transpose(matrix):
    return [list(i) for i in zip(*matrix)]

@app.context_processor
def inject():
    from dudel.views import get_locale
    return dict(
        ICONS=ICONS,
        login_form=LoginForm(),
        lang_form=LanguageForm(),
        enumerate=enumerate,
        lang=get_locale()
        )
