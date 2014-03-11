from raven.contrib.flask import Sentry
from flask import Flask
from flask.ext.babel import Babel
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown
from flask.ext.login import LoginManager, current_user
from flask.ext.gravatar import Gravatar

app = Flask(__name__)
app.config.from_pyfile("../config.py", silent=True)
db = SQLAlchemy(app)
markdown = Markdown(app, safe_mode="escape")
login_manager = LoginManager(app)
sentry = Sentry(app)
gravatar = Gravatar(app, size=48, rating='g', default='identicon', force_default=False, use_ssl=False, base_url=None)
babel = Babel(app)
supported_languages = ['en', 'de']

from dudel.util import load_icons
ICONS = load_icons("dudel/icons.txt")

import dudel.models
import dudel.forms
import dudel.filters
import dudel.views
import dudel.admin

login_manager.login_view = "login"
