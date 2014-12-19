from raven.contrib.flask import Sentry
from flask import Flask
from flask.ext.assets import Environment, Bundle
from flask.ext.babel import Babel
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown
from flask.ext.login import LoginManager, current_user
from flask.ext.gravatar import Gravatar
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Command
from flask.ext.mail import Mail

app = Flask(__name__)
app.config.from_pyfile("../config.py.example", silent=True)
app.config.from_pyfile("../config.py", silent=True)
manager = Manager(app)
db = SQLAlchemy(app)
markdown = Markdown(app, safe_mode="escape")
login_manager = LoginManager(app)
sentry = Sentry(app)
gravatar = Gravatar(app, size=48, rating='g', default='identicon', force_default=False, use_ssl=True, base_url=None)
babel = Babel(app)
supported_languages = ['en', 'de']
migrate = Migrate(app, db)
manager.add_command("db", MigrateCommand)
mail = Mail(app)
assets = Environment(app)

scss = Bundle('scss/*.scss', filters='scss', output='gen/main.css')
assets.register('scss_all', scss)
css = Bundle(
    'css/bootstrap.css',
    'css/font-awesome.css',
    'css/jquery-ui.css',
    'css/jquery-ui-timepicker-addon.css',
    'css/jquery.colorpicker.css',
    scss,
    output='gen/all.css')
assets.register('css_all', css)

from dudel.util import load_icons
ICONS = load_icons("dudel/icons.txt")

import dudel.models
import dudel.forms
import dudel.filters
import dudel.views
import dudel.admin
import dudel.plugins.ldapauth

login_manager.login_view = "login"
