from dudel import app, ICONS
from dudel.forms import LoginForm, LanguageForm
from flask import g
from flask.ext.babel import format_date, format_time, get_locale
from json import dumps

date_formats = {'de': 'EEE, dd. MMM'}

@app.template_filter()
def date(s, rebase=True):
    return format_date(s,
                       date_formats.get(get_locale().language, 'EEE, dd MMM'),
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

@app.context_processor
def inject():
    return dict(
        ICONS=ICONS,
        login_form=LoginForm(),
        lang_form=LanguageForm()
        )
