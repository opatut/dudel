from raven.contrib.flask import Sentry
from flask import Flask
from flask.ext.babel import Babel
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown
from flask.ext.login import LoginManager
from flask.ext.gravatar import Gravatar
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask.ext.mail import Mail
import pytz

app = Flask(__name__)
app.config.from_pyfile("../config.py.example", silent=True)
app.config.from_pyfile("../config.py", silent=True)
manager = Manager(app)
db = SQLAlchemy(app)
markdown = Markdown(app, safe_mode="escape")
login_manager = LoginManager(app)
if app.config.get('SENTRY_DSN', None):
    sentry = Sentry(app)
else:
    sentry = None

from .csrf import Protector
csrf = Protector(app, abort_code=403, consume=app.config.get('CSRF_CONSUME', False))
csrf.inject_as('CSRF') # make token available in template

gravatar = Gravatar(app, size=48, rating='g', default='identicon', force_default=False, use_ssl=True, base_url=None)
babel = Babel(app)
supported_languages = ['en', 'de']
migrate = Migrate(app, db)
manager.add_command("db", MigrateCommand)
mail = Mail(app)
default_timezone = pytz.timezone(app.config["DEFAULT_TIMEZONE"])

from dudel.util import load_icons
ICONS = load_icons("dudel/icons.txt")

import dudel.assets
import dudel.models
import dudel.forms
import dudel.filters
import dudel.views
import dudel.admin
import dudel.plugins.ldapauth

login_manager.login_view = "login"
